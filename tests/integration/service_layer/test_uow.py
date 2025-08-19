from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.events import TaskStarted
from src.domain.model import Task
from src.service_layer.publishing_uow import PublishingUoW
from src.service_layer.sqlalchemy_uow import SessionFactory, SQLAlchemyUoW
from src.shared.types import UUID, Model, TaskStatus


class CustomException(Exception):
    pass


def _add_task(
    session: Session,
    task_id: Optional[UUID] = None,
    owner_id: Optional[int] = None,
    filesystem: Optional[Path] = None,
    task_status: Optional[TaskStatus] = None,
    created_at: Optional[datetime] = None,
):
    task_id = task_id or UUID("task-id")
    owner_id = owner_id or 1
    filesystem = filesystem or Path(".")
    task_status = task_status or TaskStatus.PENDING
    created_at = created_at or datetime.now()

    session.execute(
        text(
            (
                "INSERT INTO tasks (id, owner_id, filesystem_path, "
                "created_at, task_status)"
                " VALUES (:task_id, :owner_id, :filesystem, "
                ":created_at, :task_status)"
            )
        ),
        dict(
            task_id=task_id,
            owner_id=owner_id,
            filesystem=str(filesystem),
            created_at=created_at,
            task_status=task_status,
        ),
    )


def test_uow_can_get(session_factory: SessionFactory):
    """
    Quickly verify that uow integrates correctly with the repository, not
    specifically getting tasks
    """
    session = session_factory()
    _add_task(session, task_id=UUID("task-id"))
    session.commit()

    uow = SQLAlchemyUoW(session_factory)
    task_id: UUID | None

    with uow:
        task = uow.tasks.get(task_id=UUID("task-id"))

        assert task is not None

        task_id = task._id
        uow.commit()

    assert task_id == UUID("task-id")


def test_uow_can_save(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    created_at = datetime.now()
    with uow:
        task = Task(
            owner_id=1,
            filesystem=Path("/filesystem"),
            created_at=created_at,
            script_path=Path("script.sh"),
            status=TaskStatus.RUNNING,
            model=Model.VTC,
            _id=UUID("abc"),
        )
        uow.tasks.save(task)
        uow.commit()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == [
        (
            "abc",
            1,
            TaskStatus.RUNNING.value,
            str(created_at),
            "/filesystem",
            "script.sh",
            Model.VTC.value,
        )
    ]


def test_uow_rolls_back_uncommitted_changes(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    created_at = datetime.now()
    with uow:
        task = Task(
            owner_id=1,
            filesystem=Path("/filesystem"),
            created_at=created_at,
        )
        uow.tasks.save(task)

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == []


def test_rolls_back_on_error(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    with pytest.raises(CustomException):
        with uow:
            _add_task(uow.session)
            raise CustomException()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == []


def test_uow_starts_task_handler(
    session_factory: SessionFactory,
):  # TODO: remove mocker when we abstract messagebus
    with patch("src.service_layer.message_bus.handle") as mock_handle:
        uow = PublishingUoW(SQLAlchemyUoW(session_factory, tracking=True))
        task_id: UUID

        with uow:
            task = Task(1, Path("."))
            uow.tasks.save(task)

            assert len(task.events) == 0
            assert task._id is not None

            task_id = task._id

            task.run()

            assert len(task.events) == 1
            assert isinstance(task.events[0], TaskStarted)
            assert task.status == TaskStatus.RUNNING

            uow.commit()

        mock_handle.assert_called_once()
        event = mock_handle.call_args[0][0]
        assert isinstance(event, TaskStarted)
        assert event.task_id == task_id
