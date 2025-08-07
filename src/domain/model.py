from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import List, Optional


class ModelName(StrEnum):
    VTC = "vtc"


class TaskType(StrEnum):
    SCRIPT = "script"
    MODEL = "model"
    UNKNOWN = "unknown"


class TaskDetails(ABC):
    """Base class for task-specific details

    Prefer to use such composition over inheritance to stay closer to the real data
    model. Classes that inherit from this represent dependent tables (i.e., with a
    foreign key to the task table)

    This generally makes mapping with the ORM much simpler as well"""

    _task_id: Optional[int] = None


# Purely semantic
TaskProperty = TaskDetails


class Task:
    owner_id: int
    created_at: datetime
    completed: bool
    filesystem: "FileSystem"
    details: Optional[TaskDetails]
    inputs: List["TaskInput"]
    outputs: List["TaskOutput"]

    _id: Optional[int]

    def __init__(
        self,
        owner_id: int,
        filesystem: "FileSystem",
        inputs: Optional[List["TaskInput"]] = None,
        outputs: Optional[List["TaskOutput"]] = None,
        created_at: Optional[datetime] = None,
        details: Optional[TaskDetails] = None,
        completed: bool = False,
        _id: Optional[int] = None,
    ):
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.created_at = created_at or datetime.now()

        self.owner_id = owner_id
        self.filesystem = filesystem
        self.details = details
        self.completed = completed

        self._id = _id

    @property
    def task_type(self) -> str:
        if isinstance(self.details, ScriptTaskDetails):
            return TaskType.SCRIPT
        elif isinstance(self.details, ModelTaskDetails):
            return TaskType.MODEL
        return TaskType.UNKNOWN

    def mark_completed(self) -> None:
        self.completed = True

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self._id == other._id

    def __hash__(self):
        return hash(self._id)


@dataclass
class EmptyTaskDetails(TaskDetails):
    pass


@dataclass
class ScriptTaskDetails(TaskDetails):
    script_path: Path


@dataclass
class ModelTaskDetails(TaskDetails):
    model_name: ModelName


@dataclass
class FileSystem(TaskProperty):
    root_abs_path: Path

    def __eq__(self, other):
        if not isinstance(other, FileSystem):
            return False

        return self.root_abs_path == other.root_abs_path

    def __hash__(self):
        return hash(self.root_abs_path)


@dataclass
class TaskInput(TaskProperty):
    rel_path: Path

    def __eq__(self, other):
        if not isinstance(other, TaskInput):
            return False

        return self.rel_path == other.rel_path

    def __hash__(self):
        return hash(self.rel_path)


@dataclass
class TaskOutput(TaskProperty):
    rel_path: Path

    def __eq__(self, other):
        if not isinstance(other, TaskOutput):
            return False

        return self.rel_path == other.rel_path

    def __hash__(self):
        return hash(self.rel_path)

    def __str__(self):
        return str(self.rel_path)
