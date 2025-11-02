from dataclasses import dataclass
from pathlib import Path

from src.config.config import ConfigModel
from src.core.types import UUID, Operation


class Command:
    task_id: UUID


@dataclass
class CreateTask(Command):
    task_id: UUID
    owner_id: UUID
    dataset: str
    operation: Operation
    config: ConfigModel

    def __eq__(self, other):
        if not isinstance(other, CreateTask):
            return NotImplemented

        return self.task_id == other.task_id

    def __hash__(self):
        return hash(self.task_id)


@dataclass
class RunTask(Command):
    task_id: UUID
    dataset: str
    script_path: Path


@dataclass
class CompleteTask(Command):
    task_id: UUID


@dataclass
class StartTask(Command):
    task_id: UUID
