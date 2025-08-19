from pathlib import Path
from typing import Optional

from src.domain.model import Task
from src.service_layer.uow import AbstractUoW
from src.shared.types import UUID, Model


def add_task(
    owner_id: int,
    filesystem: Path,
    uow: AbstractUoW,
    script_path: Optional[Path] = None,
    model: Optional[Model] = None,
) -> UUID:
    task = Task(
        owner_id=owner_id, filesystem=filesystem, model=model, script_path=script_path
    )

    with uow:
        uow.tasks.save(task)

        uow.commit()

    return task._id


def mark_task_complete(
    task_id: UUID,
    uow: AbstractUoW,
) -> None:
    with uow:
        task = uow.tasks.get(task_id)

        if not task:
            return

        if task.completed:
            return

        uow.tasks.save(task)

        uow.commit()


def mark_task_running(
    task_id: UUID,
    uow: AbstractUoW,
) -> None:
    task = uow.tasks.get(task_id)

    if not task:
        return

    if task.running:
        return

    uow.tasks.save(task)

    uow.commit()
