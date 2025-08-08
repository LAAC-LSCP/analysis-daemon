from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.model import FileSystem, Task
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
