import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.shared.types import UUID, Model, TaskStatus


class Task:
    owner_id: int
    created_at: datetime
    filesystem: Path
    status: TaskStatus
    script_path: Optional[Path]
    model: Optional[Model]

    _id: UUID

    def __init__(
        self,
        owner_id: int,
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

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_failed(self, e: Exception) -> None:
        self.status = TaskStatus.FAILED

    def get_full_script_path(self) -> Path | None:
        if self.script_path is None:
            return None

        return self.filesystem / self.script_path

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self._id == other._id

    def __hash__(self):
        return hash(self._id)
