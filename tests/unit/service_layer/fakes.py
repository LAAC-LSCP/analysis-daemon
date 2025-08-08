from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.adapters.repository import AbstractRepository
from src.domain.model import FileSystem, Task, TaskDetails, TaskInput, TaskOutput


@dataclass
class TaskArgs:
    owner_id: int
    filesystem: Path
    inputs: List[Path] = field(default_factory=list)
    outputs: List[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    details: Optional[TaskDetails] = None
    completed: bool = False
    _id: Optional[int] = None


class FakeRepository(AbstractRepository):
    """
    Fake repository for the purpose of testing
    """

    _tasks: List[Task]

    """
    A factory method that decouples us from using domain objects directly
    """

    @staticmethod
    def for_tasks(tasks: List[TaskArgs]):
        return FakeRepository(
            [
                Task(
                    owner_id=t.owner_id,
                    filesystem=FileSystem(t.filesystem),
                    inputs=[TaskInput(i) for i in t.inputs],
                    outputs=[TaskOutput(o) for o in t.outputs],
                    created_at=t.created_at,
                    details=t.details,
                    _id=t._id,
                )
                for t in tasks
            ]
        )

    def __init__(self, tasks: Optional[List[Task]] = None):
        super().__init__()
        self._tasks = []

        for task in tasks or []:
            self.save(task)

    def _get(self, task_id: int) -> Optional[Task]:
        return next((t for t in self._tasks if t._id == task_id), None)

    def _get_by_owner(self, owner_id: int) -> List[Task]:
        return [t for t in self._tasks if t.owner_id == owner_id]

    def _get_by_filesystem(self, filesystem: FileSystem) -> List[Task]:
        return [t for t in self._tasks if t.filesystem == filesystem]

    def _save(self, task: Task) -> Task:
        if task._id is None:
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
