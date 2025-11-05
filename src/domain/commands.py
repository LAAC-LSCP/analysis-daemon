from dataclasses import dataclass

from src.core.operations.operation import Operation
from src.core.types import UUID, TaskStatus


class Command:
    task_id: UUID


@dataclass
class CreateTask(Command):
    task_id: UUID
    owner_id: UUID
    dataset: str
    operation: Operation

    @property
    def status(self) -> TaskStatus:
        return TaskStatus.PENDING

    def __eq__(self, other):
        if not isinstance(other, CreateTask):
            return NotImplemented

        return self.task_id == other.task_id

    def __hash__(self):
        return hash(self.task_id)


@dataclass
class RunTask(Command):
    task_id: UUID
    operation: Operation


@dataclass
class CompleteTask(Command):
    task_id: UUID


@dataclass
class StartTask(Command):
    task_id: UUID
