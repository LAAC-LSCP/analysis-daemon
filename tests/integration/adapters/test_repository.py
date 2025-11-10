from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import src.domain.model as model
from src.adapters.sqlalchemy_repository import SQLAlchemyRepository
from src.config.config import ConfigModel
from src.core.types import UUID, TaskStatus


def test_repository_saves_task(session: Session, config_model: ConfigModel):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        dataset="loann_2025",
        created_at=dt,
        status=model.TaskStatus.PENDING,
        operation=model.Operation.VTC,
        input_folder=Path("/my_input_folder"),
        input_files=[
            Path("/my_input_folder/file_1.wav"),
            Path("/my_input_folder/file_2.wav"),
        ],
        _id=UUID("abc"),
        config=config_model,
    )

    repo.save(task)
    session.commit()

    rows = session.execute(
        text(
            "SELECT id, owner_id, task_status, created_at, operation, input_folder FROM"
            " tasks"
        )
    )
    assert list(rows) == [
        (
            "abc",
            "owner",
            model.TaskStatus.PENDING.value,
            str(dt),
            model.Operation.VTC.value,
            "/my_input_folder",
        )
    ]


def test_repository_overwrite_task(session: Session, config_model: ConfigModel):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        dataset="loann_2025",
        created_at=dt,
        status=model.TaskStatus.RUNNING,
        operation=model.Operation.VTC,
        input_folder=Path("/my_input_folder"),
        _id=UUID("abc"),
        config=config_model,
    )

    repo.save(task)
    session.commit()

    assert task._id == "abc"

    task.mark_completed()

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_status FROM tasks"))
    assert list(rows) == [("abc", "completed")]


def test_repository_mark_task_completed(session: Session, config_model: ConfigModel):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        created_at=dt,
        dataset="loann_2025",
        status=TaskStatus.PENDING,
        operation=model.Operation.VTC,
        input_folder=Path("/my_input_folder"),
        _id=UUID("abc"),
        config=config_model,
    )

    repo.save(task)
    session.commit()

    assert task._id == "abc"

    task.mark_completed()

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_status FROM tasks"))
    assert list(rows) == [("abc", model.TaskStatus.COMPLETED)]


def test_repository_saves_multiple_tasks(session: Session, config_model: ConfigModel):
    repo = SQLAlchemyRepository(session)

    task_1 = model.Task(
        owner_id=UUID("owner"),
        dataset="loann_2025",
        status=TaskStatus.PENDING,
        operation=model.Operation.VTC,
        _id=UUID("abc"),
        config=config_model,
        input_folder=Path("/my_input_folder"),
    )
    task_2 = model.Task(
        owner_id=UUID("owner"),
        dataset="loann_2025",
        status=TaskStatus.PENDING,
        operation=model.Operation.VTC,
        _id=UUID("def"),
        config=config_model,
        input_folder=Path("/my_other_folder"),
    )

    repo.save(task_1)
    repo.save(task_2)
    session.commit()

    rows = session.execute(text("SELECT id from tasks"))
    assert list(rows) == [("abc",), ("def",)]


def test_repository_get_task(session: Session, config_model: ConfigModel):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        dataset="loann_2025",
        created_at=dt,
        status=model.TaskStatus.PENDING,
        operation=model.Operation.VTC,
        _id=UUID("abc"),
        config=config_model,
        input_folder=Path("/my_input_folder"),
        input_files=[
            Path("/my_input_folder/file_1.wav"),
            Path("/my_input_folder/file_2.wav"),
        ],
    )

    repo.save(task)
    session.commit()

    saved_task = repo.get(task_id=UUID("abc"))
    assert saved_task is not None
    assert saved_task == task
    assert (
        saved_task.input_files[0].file_path,
        saved_task.input_files[1].file_path,
    ) == (Path("/my_input_folder/file_1.wav"), Path("/my_input_folder/file_2.wav"))


def test_repository_get_by_owner(
    session: Session, simple_task_factory: Callable[[UUID, UUID], model.Task]
):
    repo = SQLAlchemyRepository(session)

    task_1 = simple_task_factory(UUID("owner_1"), UUID("1"))
    task_2 = simple_task_factory(UUID("owner_1"), UUID("2"))

    repo.save(task_1)
    repo.save(task_2)
    session.commit()

    saved_tasks = repo.get_by_owner(owner_id=UUID("owner_1"))
    assert saved_tasks is not None
    assert saved_tasks == [task_1, task_2]


def test_repository_get_by_owners(
    session: Session, simple_task_factory: Callable[[UUID, UUID], model.Task]
):
    repo = SQLAlchemyRepository(session)

    task_1 = simple_task_factory(UUID("owner_1"), UUID("1"))
    task_2 = simple_task_factory(UUID("owner_1"), UUID("2"))
    task_3 = simple_task_factory(UUID("owner_2"), UUID("3"))
    task_4 = simple_task_factory(UUID("owner_2"), UUID("4"))

    repo.save(task_1)
    repo.save(task_2)
    repo.save(task_3)
    repo.save(task_4)
    session.commit()

    saved_tasks = repo.get_by_owners(owner_ids={UUID("owner_1"), UUID("owner_2")})
    assert saved_tasks is not None
    assert saved_tasks == [task_1, task_2, task_3, task_4]


def test_repository_get_by_status(
    session: Session,
    simple_task_factory: Callable[[UUID, UUID, Optional[TaskStatus]], model.Task],
):
    repo = SQLAlchemyRepository(session)

    task_1 = simple_task_factory(UUID("owner_1"), UUID("1"), TaskStatus.RUNNING)
    task_2 = simple_task_factory(UUID("owner_2"), UUID("2"), TaskStatus.PENDING)

    repo.save(task_1)
    repo.save(task_2)
    session.commit()

    running_tasks = repo.get_by_status(TaskStatus.RUNNING)
    pending_tasks = repo.get_by_status(TaskStatus.PENDING)

    assert running_tasks is not None and pending_tasks is not None
    assert [running_tasks, pending_tasks] == [[task_1], [task_2]]


@pytest.fixture
def simple_task_factory() -> Callable[[UUID, UUID, Optional[TaskStatus]], model.Task]:
    def factory(
        owner_id: UUID, _id: UUID, status: Optional[TaskStatus] = None
    ) -> model.Task:
        status = status or TaskStatus.PENDING

        return model.Task(
            owner_id=owner_id,
            dataset="loann_2025",
            created_at=datetime.now(),
            status=status,
            operation=model.Operation.VTC,
            input_folder=Path("."),
            _id=_id,
        )

    return factory
