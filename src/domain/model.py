import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.config.config import ConfigModel
from src.core import response_types
from src.core.filesystem import get_output_dir
from src.core.types import UUID, Operation, TaskStatus
from src.domain.commands import CheckTask, Command, CompleteTask, RunTask
from src.domain.events import Event, TaskCompleted, TaskCreated, TaskFailed, TaskStarted


class InputFile:
    task_id: UUID
    file_path: Path
    _id: UUID

    def __init__(self, task_id: UUID, file_path: Path, _id: Optional[UUID] = None):
        self.task_id = task_id
        self.file_path = file_path
        self._id = _id or UUID(str(uuid.uuid4()))


class Task:
    owner_id: UUID
    created_at: datetime
    dataset: str
    status: TaskStatus
    operation: Operation
    events: List[Event]
    commands: List[Command]
    input_folder: Path
    input_files: List[InputFile]
    _id: UUID

    def __init__(
        self,
        owner_id: UUID,
        dataset: str,
        status: TaskStatus,
        operation: Operation,
        input_folder: Path,
        input_files: Optional[List[Path]] = None,
        config: Optional[ConfigModel] = None,
        created_at: Optional[datetime] = None,
        _id: Optional[UUID] = None,
    ):
        self.created_at = created_at or datetime.now()
        self.status = status or TaskStatus.PENDING
        self._id = _id or UUID(str(uuid.uuid4()))
        self.operation = operation
        self.input_folder = input_folder

        if input_files is not None:
            self.input_files = [
                InputFile(task_id=self._id, file_path=path) for path in input_files
            ]
        else:
            self.input_files = []

        self.owner_id = owner_id
        self.dataset = dataset

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

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED

        self.events.append(
            TaskCompleted(
                task_id=self._id,
            )
        )

    def queue_task(self, config: ConfigModel) -> None:
        self.status = TaskStatus.PENDING

        self.events.append(
            TaskCreated(
                task_id=self._id,
            )
        )
        self.commands.append(
            RunTask(
                task_id=self._id,
                input_folder=self.input_folder,
                input_files=[file.file_path for file in self.input_files],
                echolalia_folder=config.echolalia_folder,
                dataset=self.dataset,
                operation=self.operation,
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

    def start_run(self, config: ConfigModel) -> None:
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

        self.queue_status_check(config)

    def queue_status_check(self, config: ConfigModel) -> None:
        self.commands.append(
            CheckTask(
                task_id=self._id,
                dataset=self.dataset,
                input_folder=self.input_folder,
                input_files=[f.file_path for f in self.input_files],
                output_folder=get_output_dir(config),
            )
        )

    def end_run(self) -> None:
        self.commands.append(CompleteTask(task_id=self._id))

    def to_response_type_task(self) -> "response_types.Task":
        return response_types.Task(
            datetime=self.created_at,
            owner_id=self.owner_id,
            model_name=self.operation,
            dataset_name=self.dataset,
            status=self.status,
            inputs=[file.file_path for file in self.input_files],
            input_folder=self.input_folder,
            id=self._id,
        )

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self._id == other._id

    def __hash__(self):
        return hash(self._id)
