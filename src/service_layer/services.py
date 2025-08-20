from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.adapters.repository import AbstractRepository
from src.domain.model import Task
from src.shared.types import UUID, Model


def add_task(
    owner_id: int,
    filesystem: Path,
    repo: AbstractRepository,
    session: Session,
    script_path: Optional[Path] = None,
    model: Optional[Model] = None,
) -> UUID:
    task = Task(
        owner_id=owner_id, filesystem=filesystem, model=model, script_path=script_path
    )

    task = repo.save(task)
    session.commit()

    return task._id


def mark_task_complete(
    task_id: UUID, repo: AbstractRepository, session: Session
) -> None:
    task = repo.get(task_id)

    if not task:
        return

    if task.completed:
        return

    repo.save(task)
    session.commit()


def mark_task_running(
    task_id: UUID, repo: AbstractRepository, session: Session
) -> None:
    task = repo.get(task_id)

    if not task:
        return

    if task.running:
        return

    repo.save(task)
    session.commit()
