from dataclasses import dataclass
from pathlib import Path

from src.core.types import UUID, Model


class Command:
    pass


@dataclass
class CreateTask(Command):
    task_id: UUID
    owner_id: UUID
    filesystem: Path
    script_path: Path
    model: Model

    def __eq__(self, other):
        if not isinstance(other, CreateTask):
            return NotImplemented

        return self.task_id == other.task_id

    def __hash__(self):
        return hash(self.task_id)


@dataclass
class RunTask(Command):
    task_id: UUID


@dataclass
class CompleteTask(Command):
    task_id: UUID


@dataclass
class StartTask(Command):
    task_id: UUID
