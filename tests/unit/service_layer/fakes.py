import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from random import Random
from typing import List, Optional

from src.adapters.repository import AbstractRepository
from src.domain.model import Task
from src.shared.types import UUID, Model, TaskStatus


@dataclass
class TaskArgs:
    owner_id: int
    filesystem: Path
    created_at: datetime = field(default_factory=datetime.now)
    status: str = TaskStatus.PENDING
    script_path: Optional[Path] = None
    model: Optional[Model] = None

    _id: Optional[UUID] = None


class FakeRepository(AbstractRepository):
    """
    Fake repository for the purpose of testing
    """

    _tasks: List[Task]
    _rnd: Random

    """
    A factory method that decouples us from using domain objects directly
    """

    @staticmethod
    def for_tasks(tasks: List[TaskArgs]):
        return FakeRepository(
            [
                Task(
                    owner_id=t.owner_id,
                    filesystem=t.filesystem,
                    created_at=t.created_at,
                    status=TaskStatus(t.status),
                    script_path=t.script_path,
                    model=t.model,
                    _id=t._id,
                )
                for t in tasks
            ]
        )

    def __init__(self, tasks: Optional[List[Task]] = None, seed: Optional[int] = None):
        self._tasks = []
        seed = seed or 0

        self._rnd = random.Random()
        self._rnd.seed(seed)

        for task in tasks or []:
            self.save(task)

    def get(self, task_id: UUID) -> Optional[Task]:
        return next((t for t in self._tasks if t._id == task_id), None)

    def get_by_owner(self, owner_id: UUID) -> List[Task]:
        return [t for t in self._tasks if t.owner_id == owner_id]

    def get_by_filesystem(self, filesystem: Path) -> List[Task]:
        return [t for t in self._tasks if t.filesystem == filesystem]

    def save(self, task: Task) -> Task:
        if not task._id:
            task = self._add_id(task)

        self._tasks.append(task)

        return task

    def _add_id(self, task: Task) -> Task:
        task._id = UUID(str(uuid.UUID(int=self._rnd.getrandbits(128), version=4)))

        return task
