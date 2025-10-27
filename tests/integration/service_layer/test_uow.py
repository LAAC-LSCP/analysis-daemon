from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.types import UUID, Model, TaskStatus
from src.domain.model import Task
from src.service_layer.unit_of_work.sqlalchemy_uow import SessionFactory, SQLAlchemyUoW


class CustomException(Exception):
    pass


def _add_task(
    session: Session,
    task_id: Optional[UUID] = None,
    owner_id: Optional[UUID] = None,
    filesystem: Optional[Path] = None,
    task_status: Optional[TaskStatus] = None,
    created_at: Optional[datetime] = None,
):
    task_id = task_id or UUID("task-id")
    owner_id = owner_id or UUID("owner")
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
            owner_id=UUID("owner"),
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
            "owner",
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
            owner_id=UUID("owner"),
            filesystem=Path("/filesystem"),
            script_path=Path("/test.sh"),
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
