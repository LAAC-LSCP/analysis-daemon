from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import List, Optional

from src.domain.events import Event, TaskCompleted, TaskFailed, TaskQueued, TaskStarted
from src.domain.exceptions import TaskHasNoIDError


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


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    owner_id: int
    created_at: datetime
    filesystem: "FileSystem"
    details: Optional[TaskDetails]
    inputs: List["TaskInput"]
    outputs: List["TaskOutput"]
    status: TaskStatus
    events: List[Event]

    _id: Optional[int]

    def __init__(
        self,
        owner_id: int,
        filesystem: "FileSystem",
        inputs: Optional[List["TaskInput"]] = None,
        outputs: Optional[List["TaskOutput"]] = None,
        created_at: Optional[datetime] = None,
        details: Optional[TaskDetails] = None,
        status: TaskStatus = TaskStatus.PENDING,
        _id: Optional[int] = None,
    ):
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.created_at = created_at or datetime.now()

        self.owner_id = owner_id
        self.filesystem = filesystem
        self.details = details
        self.status = status

        self._id = _id

        self.events = []

    @property
    def task_type(self) -> str:
        if isinstance(self.details, ScriptTaskDetails):
            return TaskType.SCRIPT
        elif isinstance(self.details, ModelTaskDetails):
            return TaskType.MODEL
        return TaskType.UNKNOWN

    @property
    def completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def start(self) -> None:
        if self._id is None:
            raise TaskHasNoIDError()

        if self.status != TaskStatus.PENDING:
            raise ValueError(
                f"Cannot start task in {self.status} state"
            )  # TODO: bit strong to raise an exception. Could raise event

        self.status = TaskStatus.RUNNING
        self.events.append(
            TaskStarted(
                task_id=self._id,
                owner_id=self.owner_id,
                filesystem=self.filesystem.root_abs_path,
                started_at=datetime.now(),
            )
        )

    def mark_completed(self) -> None:
        # TODO: It's clear to me we have awkward temporal coupling coming from ids
        # We should switch to UUID as is standard practice,
        # and let the constructor generate ids for us if necessary. Besides,
        # we have tricky issues with concurrency and id collisions to think about
        # otherwise
        if self._id is None:
            raise TaskHasNoIDError()

        self.status = TaskStatus.COMPLETED
        self.events.append(
            TaskCompleted(
                task_id=self._id,
                owner_id=self.owner_id,
                completed_at=datetime.now(),
                outputs=[o.rel_path for o in self.outputs],
            )
        )

    def mark_failed(self, e: Exception) -> None:
        if self._id is None:
            raise TaskHasNoIDError()

        self.status = TaskStatus.FAILED
        self.events.append(
            TaskFailed(
                task_id=self._id,
                error_message=f"Task with id {self._id} failed: {repr(e)}",
                failed_at=datetime.now(),
            )
        )

    def mark_pending(self) -> None:
        self.status = TaskStatus.PENDING
        self.events.append(
            TaskQueued(
                owner_id=self.owner_id,
                filesystem=self.filesystem.root_abs_path,
                inputs=[i.rel_path for i in self.inputs],
                outputs=[o.rel_path for o in self.outputs],
                task_id=self._id,
            )
        )

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
