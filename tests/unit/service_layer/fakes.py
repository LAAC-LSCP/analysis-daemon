from typing import List, Optional

from src.adapters.repository import AbstractRepository
from src.domain.model import FileSystem, Task


class FakeRepository(AbstractRepository):
    """
    Fake repository for the purpose of testing
    """

    _tasks: List[Task]

    def __init__(self, tasks: Optional[List[Task]] = None):
        self._tasks = []

        for task in tasks or []:
            self.save(task)

    def get(self, task_id: int) -> Optional[Task]:
        return next((t for t in self._tasks if t._id == task_id), None)

    def get_by_owner(self, owner_id: int) -> List[Task]:
        return [t for t in self._tasks if t.owner_id == owner_id]

    def get_by_filesystem(self, filesystem: FileSystem) -> List[Task]:
        return [t for t in self._tasks if t.filesystem == filesystem]

    def save(self, task: Task) -> Task:
        task = self._add_id(task)

        self._tasks.append(task)

        return task

    def _add_id(self, task: Task) -> Task:
        id: int = max([t._id for t in self._tasks if t._id is not None], default=0) + 1
        task._id = id

        return task


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True
