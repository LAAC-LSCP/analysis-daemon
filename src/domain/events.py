from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class Event:
    pass


@dataclass
class TaskCreated(Event):
    owner_id: int
    filesystem: Path
    started_at: datetime = field(default_factory=datetime.now)
    inputs: List[Path] = field(default_factory=list)
    outputs: List[Path] = field(default_factory=list)
    task_id: Optional[int] = None


@dataclass
class MarkTaskAsCompleted(Event):
    task_id: int


@dataclass
class TaskStarted(Event):
    task_id: int
    owner_id: int
    filesystem: Path
    started_at: datetime


@dataclass
class TaskCompleted(Event):
    task_id: int
    owner_id: int
    completed_at: datetime
    outputs: List[Path]


@dataclass
class TaskFailed(Event):
    task_id: int
    error_message: str
    failed_at: datetime
