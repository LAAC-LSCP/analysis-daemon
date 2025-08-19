from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.shared.types import UUID


class Event:
    pass


@dataclass
class TaskStarted(Event):
    task_id: UUID
    owner_id: int
    filesystem: Path
    started_at: datetime


@dataclass
class TaskCompleted(Event):
    task_id: UUID
    owner_id: int
    completed_at: datetime


@dataclass
class TaskFailed(Event):
    task_id: UUID
    error_message: str
    failed_at: datetime
