from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


class Event:
    pass


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
