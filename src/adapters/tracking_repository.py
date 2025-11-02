from typing import Generic, List, Optional, Set

from src.adapters.repository import AbstractRepository
from src.core.types import UUID, TaskStatus
from src.domain.model import Task
from src.service_layer.types import RepoType


class TrackingRepository(AbstractRepository, Generic[RepoType]):
    """
    Decorator that adds tracking to a repository

    Tracking is powerful when we need to remember what tasks have already been
    "handled", for instance when we repeatedly collect new events or commands added to
    the associated unit of work
    """

    seen: Set[Task]
    _repository: RepoType

    def __init__(self, repository: RepoType):
        self.seen = set()
        self._repository = repository

    def get(self, task_id: UUID) -> Optional[Task]:
        task = self._repository.get(task_id)

        if task:
            self.seen.add(task)

        return task

    def get_by_owner(self, owner_id: UUID) -> List[Task]:
        tasks = self._repository.get_by_owner(owner_id)

        if tasks:
            self.seen.update(tasks)

        return tasks

    def get_by_owners(self, owner_ids: Set[UUID]) -> List[Task]:
        tasks = self._repository.get_by_owners(owner_ids)

        if tasks:
            self.seen.update(tasks)

        return tasks

    def get_by_dataset(self, dataset: str) -> List[Task]:
        tasks = self._repository.get_by_dataset(dataset)

        if tasks:
            self.seen.update(tasks)

        return tasks

    def get_by_status(self, status: TaskStatus) -> List[Task]:
        tasks = self._repository.get_by_status(status)

        if tasks:
            self.seen.update(tasks)

        return tasks

    def save(self, task: Task) -> Task:
        task = self._repository.save(task)

        # Discard because otherwise tasks cannot update
        self.seen.discard(task)
        self.seen.add(task)

        return task
