from datetime import datetime
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.types import UUID, Operation, TaskStatus
from src.domain.model import Task
from src.service_layer.unit_of_work.sqlalchemy_uow import SessionFactory, SQLAlchemyUoW


class CustomException(Exception):
    pass


def _add_task(
    session: Session,
    dataset: str,
    status: TaskStatus,
    operation: Operation,
    config_version: Optional[int] = None,
    task_id: Optional[UUID] = None,
    owner_id: Optional[UUID] = None,
    created_at: Optional[datetime] = None,
):
    dataset = dataset
    status = status
    operation = operation

    task_id = task_id or UUID("task-id")
    owner_id = owner_id or UUID("owner")
    created_at = created_at or datetime.now()
    config_version = config_version or 1

    session.execute(
        text(
            (
                "INSERT INTO tasks (id, owner_id, dataset, "
                "operation, created_at, task_status, config_version)"
                " VALUES (:task_id, :owner_id, :dataset, "
                ":operation, :created_at, :task_status, :config_version)"
            )
        ),
        dict(
            task_id=task_id,
            owner_id=owner_id,
            dataset=dataset,
            operation=operation,
            created_at=created_at,
            task_status=status,
            config_version=config_version,
        ),
    )


def test_uow_can_get(session_factory: SessionFactory):
    """
    Quickly verify that uow integrates correctly with the repository, not
    specifically getting tasks
    """
    session = session_factory()
    _add_task(
        session,
        dataset="loann_2025",
        task_id=UUID("task-id"),
        operation=Operation.VTC,
        status=TaskStatus.PENDING,
    )
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
            dataset="loann_2025",
            created_at=created_at,
            status=TaskStatus.RUNNING,
            operation=Operation.VTC,
            config_version=0,
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
            "loann_2025",
            Operation.VTC.value,
            0,
        )
    ]


def test_uow_rolls_back_uncommitted_changes(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    created_at = datetime.now()
    with uow:
        task = Task(
            owner_id=UUID("owner"),
            dataset="loann_2025",
            created_at=created_at,
            operation=Operation.VTC,
            status=TaskStatus.PENDING,
            config_version=0,
        )
        uow.tasks.save(task)

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == []


def test_rolls_back_on_error(session_factory: SessionFactory):
    uow = SQLAlchemyUoW(session_factory)
    with pytest.raises(CustomException):
        with uow:
            _add_task(
                uow.session,
                dataset="loann_2025",
                operation=Operation.VTC,
                status=TaskStatus.PENDING,
            )
            raise CustomException()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == []
