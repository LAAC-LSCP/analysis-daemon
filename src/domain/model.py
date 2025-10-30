import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.config.config import ConfigModel
from src.core import response_types
from src.core.types import UUID, Model, TaskStatus
from src.domain.commands import Command, CompleteTask, RunTask
from src.domain.events import Event, TaskCompleted, TaskCreated, TaskFailed, TaskStarted


class Task:
    owner_id: UUID
    created_at: datetime
    filesystem: Path
    status: TaskStatus
    script_path: Path
    model: Model
    events: List[Event]
    commands: List[Command]

    _id: UUID

    def __init__(
        self,
        owner_id: UUID,
        filesystem: Path,
        script_path: Path,
        created_at: Optional[datetime] = None,
        status: Optional[TaskStatus] = None,
        model: Optional[Model] = None,
        _id: Optional[UUID] = None,
    ):
        self.created_at = created_at or datetime.now()
        self.status = status or TaskStatus.PENDING
        self._id = _id or UUID(str(uuid.uuid4()))
        self.model = model or Model.UNKNOWN

        self.script_path = script_path
        self.owner_id = owner_id
        self.filesystem = filesystem

        self.events = []
        self.commands = []

    @property
    def completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def running(self) -> bool:
        return self.status == TaskStatus.RUNNING

    @property
    def failed(self) -> bool:
        return self.status == TaskStatus.FAILED

    @property
    def pending(self) -> bool:
        return self.status == TaskStatus.PENDING

    @property
    def full_script_path(self) -> Path | None:
        if self.script_path is None:
            return None

        return self.filesystem / self.script_path

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED

        self.events.append(
            TaskCompleted(
                task_id=self._id,
            )
        )

    def queue_task(self) -> None:
        self.status = TaskStatus.PENDING

        self.events.append(
            TaskCreated(
                task_id=self._id,
            )
        )
        self.commands.append(
            RunTask(
                task_id=self._id,
                script_path=self.script_path,
                filesystem_path=self.filesystem,
            )
        )

    def mark_failed(self, e: Exception) -> None:
        self.status = TaskStatus.FAILED

        self.events.append(
            TaskFailed(
                task_id=self._id,
                stack_trace=f"Task with id {self._id} failed: {repr(e)}",
            )
        )

    def start_run(self) -> None:
        if self.status != TaskStatus.PENDING:
            raise ValueError(
                f"Cannot start task in {self.status} state"
            )  # TODO: bit strong to raise an exception. Could raise event later

        self.status = TaskStatus.RUNNING

        self.events.append(
            TaskStarted(
                task_id=self._id,
            )
        )

    def end_run(self) -> None:
        self.commands.append(CompleteTask(task_id=self._id))

    # TODO: is "network" not a better word here?
    def to_response_type_task(self, config: ConfigModel) -> "response_types.Task":
        dataset_name: str | None = next(
            (
                fs.dataset_name
                for fs in config.filesystems
                if fs.path == Path(self.filesystem)
            ),
            None,
        )

        if dataset_name is None:
            raise ValueError(f"No filesystem found with path {str(self.filesystem)}")

        return response_types.Task(
            datetime=self.created_at,
            owner_id=self.owner_id,
            model_name=self.model,
            dataset_name=dataset_name,
            status=self.status,
            id=self._id,
        )

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self._id == other._id

    def __hash__(self):
        return hash(self._id)


class Config:
    version: int
    data: Dict
    created_at: datetime

    def __init__(self, version: int, data: Dict, created_at: Optional[datetime] = None):
        self.version = version
        self.data = data
        self.created_at = created_at or datetime.now()
