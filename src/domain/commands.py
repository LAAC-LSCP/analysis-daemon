from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class Command:
    pass


@dataclass
class CreateTask(Command):
    owner_id: int
    filesystem: Path
    inputs: List[Path] = field(default_factory=list)
    outputs: List[Path] = field(default_factory=list)
    task_id: Optional[int] = None


@dataclass
class MarkTaskAsComplete(Command):
    task_id: str


@dataclass
class StartTask(Command):
    task_id: str
