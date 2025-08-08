from abc import ABC, abstractmethod
from typing import List, Optional, Set

from src.domain.model import FileSystem, Task


class AbstractRepository(ABC):
    """
    An abstract base class for a task repository
    """

    # TODO: Bit messy. Might add a TrackingRepository class?
    seen: Set[Task]

    def __init__(self):
        self.seen = set()

    def get(self, task_id: int) -> Optional[Task]:
        task = self._get(task_id)
        if task:
            self.seen.add(task)

        return task

    def get_by_owner(self, owner_id: int) -> List[Task]:
        tasks = self._get_by_owner(owner_id)
        if tasks:
            self.seen.update(tasks)

        return tasks

    def get_by_filesystem(self, filesystem: FileSystem) -> List[Task]:
        tasks = self._get_by_filesystem(filesystem)
        if tasks:
            self.seen.update(tasks)

        return tasks

    def save(self, task: Task) -> Task:
        task = self._save(task)
        self.seen.add(task)

        return task

    @abstractmethod
    def _get(self, task_id: int) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def _get_by_owner(self, owner_id: int) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def _get_by_filesystem(self, filesystem: FileSystem) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def _save(self, task: Task) -> Task:
        raise NotImplementedError
