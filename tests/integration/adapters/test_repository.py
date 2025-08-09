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
        details=model.ScriptTaskDetails(Path(".")),
        filesystem=model.FileSystem(Path(".")),
        created_at=dt,
    )

    repo.save(task)
    session.commit()

    rows = session.execute(
        text("SELECT id, owner_id, created_at, task_status FROM tasks")
    )
    assert list(rows) == [(1, 5, str(dt), model.TaskStatus.PENDING)]


def test_repository_overwrite_task(session: Session):
    dt = datetime.now()
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(Path(".")),
        filesystem=model.FileSystem(Path(".")),
        created_at=dt,
    )

    repo.save(task)
    session.commit()

    assert task._id == 1

    task.mark_completed()

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_status FROM tasks"))
    assert list(rows) == [(1, "completed")]


def test_repository_saves_multiple_tasks(session: Session):
    """
    This test also tests that the `flush` call in the repo doesn't cancel the whole
    transaction

    SQLAlchemy performs some hidden magic to make this work
    """
    repo = SQLAlchemyRepository(session)

    task_1 = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(Path("path1")),
        filesystem=model.FileSystem(Path(".")),
    )
    task_2 = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(Path("path2")),
        filesystem=model.FileSystem(Path(".")),
    )

    repo.save(task_1)
    repo.save(task_2)
    session.commit()

    rows = session.execute(
        text("SELECT task_id, script_file_rel_path FROM script_tasks")
    )
    assert list(rows) == [(1, "path1"), (2, "path2")]


def test_repository_saves_task_details(session: Session):
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(Path(".")),
        filesystem=model.FileSystem(Path(".")),
        _id=5,
    )

    repo.save(task)
    session.commit()

    rows = session.execute(
        text("SELECT task_id, script_file_rel_path FROM script_tasks")
    )
    assert list(rows) == [(5, ".")]


def test_repository_saves_filesystem(session: Session):
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(script_path=Path(".")),
        filesystem=model.FileSystem(Path("/my/path")),
    )

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, root_abs_path FROM filesystems"))
    assert list(rows) == [(1, "/my/path")]


def test_repository_saves_inputs(session: Session):
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(script_path=Path(".")),
        filesystem=model.FileSystem(Path("/my/path")),
        inputs=[model.TaskInput(Path("/input_1")), model.TaskInput(Path("/input_2"))],
    )

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_id, rel_path FROM inputs"))
    assert list(rows) == [(1, 1, "/input_1"), (2, 1, "/input_2")]


def test_repository_saves_outputs(session: Session):
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(script_path=Path(".")),
        filesystem=model.FileSystem(Path("/my/path")),
        outputs=[
            model.TaskOutput(Path("/output_1")),
            model.TaskOutput(Path("/output_2")),
        ],
    )

    repo.save(task)
    session.commit()

    rows = session.execute(text("SELECT id, task_id, rel_path FROM outputs"))
    assert list(rows) == [(1, 1, "/output_1"), (2, 1, "/output_2")]


def test_repository_get_task(session: Session):
    repo = SQLAlchemyRepository(session)
    task = model.Task(
        owner_id=1,
        details=model.ScriptTaskDetails(Path(".")),
        filesystem=model.FileSystem(Path("/my/path")),
    )

    repo.save(task)

    saved_task = repo.get(task_id=1)
    assert saved_task is not None
    assert saved_task.details == model.ScriptTaskDetails(Path("."))
