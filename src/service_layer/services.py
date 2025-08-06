from typing import List, Set, cast

from sqlalchemy.orm import Session

from src.adapters.sqlalchemy_repository import SQLAlchemyRepository
from src.domain.exceptions import TaskCollisionError
from src.domain.model import Task, TaskOutput

_active_tasks: Set[Task] = set()


def add_task(task: Task, repo: SQLAlchemyRepository, session: Session) -> int:
    if conflicts := collisions(task, repo):
        raise TaskCollisionError(task.filesystem, conflicts)

    task = repo.save(task)
    _active_tasks.add(task)
    session.commit()

    return cast(int, task._id)


def mark_task_complete(
    task: Task, repo: SQLAlchemyRepository, session: Session
) -> None:
    if task.completed:
        return

    task.completed = True

    repo.save(task)
    _active_tasks.discard(task)
    session.commit()


def get_active_tasks() -> Set[Task]:
    return _active_tasks.copy()


def collisions(task: Task, repo: SQLAlchemyRepository) -> Set[TaskOutput]:
    """
    Check for collisions

    Collisions are present for tasks that:
    - run on the same filesystem
    - not yet completed
    - sharing some output with the output of the task at hand
    """
    tasks: List[Task] = repo.get_by_filesystem(task.filesystem)

    if not tasks:
        return set()

    running_tasks = [t for t in tasks if not t.completed]

    running_task_outputs = set([output for t in running_tasks for output in t.outputs])
    task_outputs = set(task.outputs)

    return running_task_outputs & task_outputs
