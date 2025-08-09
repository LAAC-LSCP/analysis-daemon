from pathlib import Path
from typing import List, Set

from src.domain.commands import MarkTaskAsComplete
from src.domain.events import TaskQueued
from src.domain.exceptions import TaskCollisionError
from src.domain.model import FileSystem, Task, TaskInput, TaskOutput
from src.service_layer.uow import AbstractUoW

_active_tasks: Set[Task] = set()


def add_task(
    event: TaskQueued,
    uow: AbstractUoW,
) -> Task:
    task: Task = Task(
        owner_id=event.owner_id,
        filesystem=FileSystem(event.filesystem),
        inputs=[TaskInput(i) for i in event.inputs],
        outputs=[TaskOutput(o) for o in event.outputs],
    )

    if collisions := _collisions(event.outputs, event.filesystem, uow):
        raise TaskCollisionError(event.filesystem, collisions)

    with uow:
        task = uow.tasks.save(task)

        _active_tasks.add(
            task
        )  # TODO: we haven't properly coupled active tasks to the uow yet
        task.mark_pending()

        uow.commit()

    return task


def mark_task_complete(
    command: MarkTaskAsComplete,
    uow: AbstractUoW,
) -> None:
    task = next((t for t in _active_tasks if t._id == command.task_id), None)

    if not task:
        return

    if task.completed:
        return

    with uow:
        task.mark_completed()

        uow.tasks.save(task)

        _active_tasks.discard(task)  # TODO: need to couple uow with active tasks

        uow.commit()


def get_active_tasks() -> Set[int]:
    return set(t._id for t in _active_tasks if t._id is not None)


def _collisions(
    task_outputs: List[Path], filesystem_root: Path, uow: AbstractUoW
) -> Set[Path]:
    """
    Check for collisions

    Collisions are present for tasks that:
    - run on the same filesystem
    - not yet completed
    - sharing some output with the output of the task at hand
    """
    tasks: List[Task] = uow.tasks.get_by_filesystem(FileSystem(filesystem_root))

    if not tasks:
        return set()

    running_tasks = [t for t in tasks if not t.completed]

    running_outputs: Set[Path] = set(
        [output.rel_path for t in running_tasks for output in t.outputs]
    )

    return running_outputs & set(task_outputs)
