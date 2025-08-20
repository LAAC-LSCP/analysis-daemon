from dataclasses import dataclass
from pathlib import Path

from src.shared.types import UUID, Model


class Command:
    pass


@dataclass
class CreateTask(Command):
    task_id: UUID
    owner_id: int
    filesystem: Path
    script_path: Path
    model: Model


@dataclass
class RunTask(Command):
    task_id: UUID


@dataclass
class CompleteTask(Command):
    task_id: UUID


@dataclass
class StartTask(Command):
    task_id: UUID
