from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.events import TaskStarted
from src.domain.model import FileSystem, Task, TaskStatus
from src.service_layer.sqlalchemy_uow import SessionFactory, SQLAlchemyUoW


class CustomException(Exception):
    pass


def _add_task(
    session: Session,
    owner_id: Optional[int] = None,
    completed: Optional[bool] = None,
    created_at: Optional[datetime] = None,
):
    owner_id = owner_id or 1
    completed = completed or True
    created_at = created_at or datetime.now()

    session.execute(
        text(
            (
                "INSERT INTO tasks (owner_id, completed, created_at)"
                " VALUES (:owner_id, :completed, :created_at)"
            )
        ),
        dict(
            owner_id=owner_id,
            completed=completed,
            created_at=created_at,
        ),
    )


def test_uow_can_get(session_factory: SessionFactory):
    """
    Quickly verify that uow integrates correctly with the repository, not specifically
    getting tasks
    """
    session = session_factory()
    _add_task(session)
    session.commit()

    uow = SQLAlchemyUoW(session_factory)
    task_id: int | None

    with uow:
        task = uow.tasks.get(task_id=1)

        assert task is not None

        task_id = task._id
        uow.commit()

    assert task_id == 1


def test_uow_starts_task_handler(
    session_factory: SessionFactory,
):  # TODO: remove mocker when we abstract messagebus
    with patch("src.service_layer.message_bus.handle") as mock_handle:
        uow = SQLAlchemyUoW(session_factory)
        task_id: int

        with uow:
            task = Task(1, FileSystem(Path(".")))
            uow.tasks.save(task)

            assert len(task.events) == 0
            assert task._id is not None

            task_id = task._id

            task.start()

            assert len(task.events) == 1
            assert isinstance(task.events[0], TaskStarted)
            assert task.status == TaskStatus.RUNNING

            uow.commit()

        mock_handle.assert_called_once()
        event = mock_handle.call_args[0][0]
        assert isinstance(event, TaskStarted)
        assert event.task_id == task_id


def test_rolls_back_uncommitted_work_by_default(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    created_at = datetime.now()
    with uow:
        task = Task(1, FileSystem(Path(".")), created_at=created_at)
        uow.tasks.save(task)
        uow.commit()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == [(1, 1, 0, str(created_at))]


def test_rolls_back_on_error(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    with pytest.raises(CustomException):
        with uow:
            _add_task(uow.session)
            raise CustomException()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == []
