from datetime import datetime
from pathlib import Path
from typing import Callable

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import src.domain.model as model
from src.adapters.sqlalchemy_repository import SQLAlchemyRepository
from src.core.types import UUID


def test_repository_saves_task(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        filesystem=Path("."),
        created_at=dt,
        status=model.TaskStatus.PENDING,
        model=model.Model.VTC,
        script_path=Path("/test.sh"),
        _id=UUID("abc"),
    )

    repo.save(task)
    session.commit()

    rows = session.execute(
        text(
            "SELECT id, owner_id, task_status, created_at, script_rel_path, model FROM"
            " tasks"
        )
    )
    assert list(rows) == [
        (
            "abc",
            "owner",
            model.TaskStatus.PENDING.value,
            str(dt),
            "/test.sh",
            model.Model.VTC.value,
        )
    ]


def test_repository_overwrite_task(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        filesystem=Path("."),
        created_at=dt,
        status=model.TaskStatus.RUNNING,
        _id=UUID("abc"),
    )

    repo.save(task)
    session.commit()

    assert task._id == "abc"

    task.mark_completed()

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_status FROM tasks"))
    assert list(rows) == [("abc", "completed")]


def test_repository_mark_task_completed(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        created_at=dt,
        filesystem=Path("."),
        _id=UUID("abc"),
    )

    repo.save(task)
    session.commit()

    assert task._id == "abc"

    task.mark_completed()

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_status FROM tasks"))
    assert list(rows) == [("abc", model.TaskStatus.COMPLETED)]


def test_repository_saves_multiple_tasks(session: Session):
    repo = SQLAlchemyRepository(session)

    task_1 = model.Task(
        owner_id=UUID("owner"),
        filesystem=Path("."),
        _id=UUID("abc"),
    )
    task_2 = model.Task(
        owner_id=UUID("owner"),
        filesystem=Path("."),
        _id=UUID("def"),
    )

    repo.save(task_1)
    repo.save(task_2)
    session.commit()

    rows = session.execute(text("SELECT id from tasks"))
    assert list(rows) == [("abc",), ("def",)]


def test_repository_get_task(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=UUID("owner"),
        filesystem=Path("."),
        created_at=dt,
        status=model.TaskStatus.PENDING,
        model=model.Model.VTC,
        script_path=Path("/test.sh"),
        _id=UUID("abc"),
    )

    repo.save(task)
    session.commit()

    saved_task = repo.get(task_id=UUID("abc"))
    assert saved_task is not None
    assert saved_task == task


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


@pytest.fixture
def simple_task_factory() -> Callable[[UUID, UUID], model.Task]:
    def factory(owner_id: UUID, _id: UUID) -> model.Task:
        return model.Task(
            owner_id=owner_id,
            filesystem=Path("."),
            created_at=datetime.now(),
            status=model.TaskStatus.PENDING,
            model=model.Model.VTC,
            script_path=Path("/test.sh"),
            _id=_id,
        )

    return factory
