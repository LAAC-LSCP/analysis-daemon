import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.types import UUID, Model, TaskStatus
from src.domain.commands import Command
from src.domain.events import Event, TaskCompleted, TaskCreated, TaskFailed, TaskStarted


class Task:
    owner_id: UUID
    created_at: datetime
    filesystem: Path
    status: TaskStatus
    script_path: Optional[Path]
    model: Optional[Model]
    events: List[Event]
    commands: List[Command]

    _id: UUID

    def __init__(
        self,
        owner_id: UUID,
        filesystem: Path,
        created_at: Optional[datetime] = None,
        status: Optional[TaskStatus] = None,
        script_path: Optional[Path] = None,
        model: Optional[Model] = None,
        _id: Optional[UUID] = None,
    ):
        self.created_at = created_at or datetime.now()
        self.status = status or TaskStatus.PENDING
        self._id = _id or UUID(str(uuid.uuid4()))
        self.script_path = script_path or None
        self.model = model or None

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

    def mark_failed(self, e: Exception) -> None:
        self.status = TaskStatus.FAILED

        self.events.append(
            TaskFailed(
                task_id=self._id,
                error_message=f"Task with id {self._id} failed: {repr(e)}",
            )
        )

    def run(self) -> None:
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

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self._id == other._id

    def __hash__(self):
        return hash(self._id)
