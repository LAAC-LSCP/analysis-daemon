from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

import src.domain.model as model
from src.adapters.sqlalchemy_repository import SQLAlchemyRepository


def test_repository_saves_task(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=5,
        filesystem=Path("."),
        created_at=dt,
        status=model.TaskStatus.PENDING,
        model=model.Model.VTC,
        script_path=Path("/test.sh"),
        _id=model.UUID("abc"),
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
            5,
            model.TaskStatus.PENDING.value,
            str(dt),
            "/test.sh",
            model.Model.VTC.value,
        )
    ]


def test_repository_mark_task_completed(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        created_at=dt,
        filesystem=Path("."),
        _id=model.UUID("abc"),
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
        owner_id=1,
        filesystem=Path("."),
        _id=model.UUID("abc"),
    )
    task_2 = model.Task(
        owner_id=1,
        filesystem=Path("."),
        _id=model.UUID("def"),
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
        owner_id=5,
        filesystem=Path("."),
        created_at=dt,
        status=model.TaskStatus.PENDING,
        model=model.Model.VTC,
        script_path=Path("/test.sh"),
        _id=model.UUID("abc"),
    )

    repo.save(task)
    session.commit()

    saved_task = repo.get(task_id=model.UUID("abc"))
    assert saved_task is not None
    assert saved_task == task
