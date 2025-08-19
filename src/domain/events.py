from dataclasses import dataclass
from pathlib import Path

from src.shared.types import UUID, Model


class Event:
    pass


@dataclass
class TaskCreated(Event):
    task_id: UUID
    owner_id: int
    filesystem: Path
    script_path: Path
    model: Model


@dataclass
class TaskStarted(Event):
    task_id: UUID


@dataclass
class TaskCompleted(Event):
    task_id: UUID


@dataclass
class TaskFailed(Event):
    task_id: UUID
    error_message: str
