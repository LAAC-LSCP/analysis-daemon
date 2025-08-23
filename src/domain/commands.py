from dataclasses import dataclass
from pathlib import Path

from src.shared.types import UUID, Model


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
        return (
            self.owner_id,
            self.filesystem,
            self.script_path,
            self.model,
        ) == (
            other.owner_id,
            other.filesystem,
            other.script_path,
            other.model,
        )

    def __hash__(self):
        return hash((self.owner_id, self.filesystem, self.script_path, self.model))


@dataclass
class RunTask(Command):
    task_id: UUID


@dataclass
class CompleteTask(Command):
    task_id: UUID


@dataclass
class StartTask(Command):
    task_id: UUID
