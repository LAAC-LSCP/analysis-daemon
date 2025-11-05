import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from random import Random
from typing import List, Optional, Set

from src.adapters.repository import AbstractRepository
from src.config.config import ConfigModel
from src.core.types import UUID, OperationName, TaskStatus
from src.domain.model import Task


@dataclass
class TaskArgs:
    owner_id: UUID
    dataset: str
    script_path: Path
    operation: OperationName
    created_at: datetime = field(default_factory=datetime.now)
    status: str = TaskStatus.PENDING
    config_version: int = 0

    _id: Optional[UUID] = None
    _config: Optional[ConfigModel] = None


class FakeRepository(AbstractRepository):
    """
    Fake repository for the purpose of testing
    """

    _tasks: List[Task]
    _config: Optional[ConfigModel]
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
                    dataset=t.dataset,
                    created_at=t.created_at,
                    status=TaskStatus(t.status),
                    operation=t.operation,
                    config_version=t.config_version,
                    _id=t._id,
                    _config=t._config,
                )
                for t in tasks
            ]
        )

    def __init__(
        self,
        tasks: Optional[List[Task]] = None,
        config: Optional[ConfigModel] = None,
        seed: Optional[int] = None,
    ):
        self._tasks = []
        self._config = config or None
        seed = seed or 0

        self._rnd = random.Random()
        self._rnd.seed(seed)

        for task in tasks or []:
            self.save(task)

    def get(self, task_id: UUID) -> Optional[Task]:
        return next((t for t in self._tasks if t._id == task_id), None)

    def get_by_owner(self, owner_id: UUID) -> List[Task]:
        return [t for t in self._tasks if t.owner_id == owner_id]

    def get_by_owners(self, owner_ids: Set[UUID]) -> List[Task]:
        return [t for t in self._tasks if t.owner_id in owner_ids]

    def get_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self._tasks if t.status == status]

    def get_by_dataset(self, dataset: str) -> List[Task]:
        return [t for t in self._tasks if t.dataset == dataset]

    def save(self, task: Task) -> Task:
        if not task._id:
            task = self._add_id(task)

        if self._config is not None:
            task._add_config(
                self._config,
                config_version=task.config_version,
                created_at=task.created_at or datetime.now(),
            )

        self._tasks.append(task)

        return task

    def _add_id(self, task: Task) -> Task:
        task._id = UUID(
            str(
                uuid.UUID(
                    int=self._rnd.getrandbits(128),
                    version=4,
                ),
            )
        )

        return task
