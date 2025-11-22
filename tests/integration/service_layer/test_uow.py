from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.types import UUID, Operation, TaskStatus
from src.domain.model import InputFile, Task
from src.service_layer.unit_of_work.sqlalchemy_uow import SessionFactory, SQLAlchemyUoW


class CustomException(Exception):
    pass


def _add_task(
    session: Session,
    dataset: str,
    status: TaskStatus,
    operation: Operation,
    input_folder: Path,
    input_files: List[Path],
    task_id: Optional[UUID] = None,
    owner_id: Optional[UUID] = None,
    created_at: Optional[datetime] = None,
):
    task_id = task_id or UUID("task-id")
    owner_id = owner_id or UUID("owner")
    created_at = created_at or datetime.now()

    session.execute(
        text(
            (
                "INSERT INTO tasks (id, owner_id, dataset, "
                "operation, created_at, task_status, input_folder)"
                " VALUES (:task_id, :owner_id, :dataset, "
                ":operation, :created_at, :task_status, :input_folder)"
            )
        ),
        dict(
            task_id=task_id,
            owner_id=owner_id,
            dataset=dataset,
            operation=operation,
            created_at=created_at,
            task_status=status,
            input_folder=str(input_folder),
        ),
    )

    for file in input_files:
        input_file = InputFile(task_id=task_id, file_path=file)

        session.execute(
            text(
                "INSERT INTO input_files (id, task_id, file_path)"
                " VALUES (:id, :task_id, :file_path)"
            ),
            dict(id=input_file._id, task_id=task_id, file_path=str(file)),
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
        input_folder=Path("/my_input_folder/"),
        input_files=[
            Path("/my_input_folder/file_1.wav"),
            Path("/my_input_folder/file_2.wav"),
        ],
    )
    session.commit()

    uow = SQLAlchemyUoW(session_factory)
    task_id: UUID | None

    with uow:
        task = uow.tasks.get(task_id=UUID("task-id"))

        assert task is not None
        assert task.dataset == "loann_2025"
        assert not task.completed
        assert not task.failed
        assert task.pending
        assert task._id == UUID("task-id")

        assert (task.input_files[0].file_path, task.input_files[1].file_path) == (
            Path("/my_input_folder/file_1.wav"),
            Path("/my_input_folder/file_2.wav"),
        )
        assert (task.input_files[0]._id, task.input_files[1]._id) == (
            task.input_files[0]._get_id(),
            task.input_files[1]._get_id(),
        )

        task_id = task._id

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
            _id=UUID("abc"),
            input_folder=Path("/my_input_folder/"),
            input_files=[
                Path("/my_input_folder/file_1.wav"),
                Path("/my_input_folder/file_2.wav"),
            ],
        )
        uow.tasks.save(task)
        uow.commit()

    new_session = session_factory()
    task_rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert task_rows == [
        (
            "abc",
            "owner",
            TaskStatus.RUNNING.value,
            str(created_at),
            "loann_2025",
            Operation.VTC.value,
            "/my_input_folder",
        )
    ]

    files_rows = list(new_session.execute(text("SELECT * FROM input_files")))
    assert [row[1:3] for row in files_rows] == [
        ("abc", "/my_input_folder/file_1.wav"),
        ("abc", "/my_input_folder/file_2.wav"),
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
            input_folder=Path("/my_input_folder/"),
            input_files=[],
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
                input_folder=Path("/my_input_folder/"),
                input_files=[
                    Path("/my_input_folder/file_1.wav"),
                    Path("/my_input_folder/file_2.wav"),
                ],
            )
            raise CustomException()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM tasks")))
    assert rows == []
