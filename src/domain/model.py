import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.config.config import ConfigModel
from src.core import response_types
from src.core.exceptions import NoFileSystemWithDataset, NoScriptWithOperation
from src.core.operations.operation import operation_factory
from src.core.types import UUID, OperationName, ScriptArgs, ScriptFlags, TaskStatus
from src.domain.commands import Command, CompleteTask, RunTask
from src.domain.events import Event, TaskCompleted, TaskCreated, TaskFailed, TaskStarted


class Task:
    owner_id: UUID
    created_at: datetime
    dataset: str
    status: TaskStatus
    operation: OperationName
    args: ScriptArgs
    flags: ScriptFlags
    config_version: int

    # NOTE: _config is retrieved on fetch of existing tasks
    # but on constructor call, not actually set by the ORM mapper
    # Ditto for _id. Hence they can be passed as arguments
    _config: Optional["Config"]
    _id: UUID

    events: List[Event]
    commands: List[Command]

    def __init__(
        self,
        owner_id: UUID,
        dataset: str,
        status: TaskStatus,
        operation: OperationName,
        config_version: int,
        args: Optional[ScriptArgs] = None,
        flags: Optional[ScriptFlags] = None,
        created_at: Optional[datetime] = None,
        _config: Optional[ConfigModel] = None,
        _id: Optional[UUID] = None,
    ):
        self.created_at = created_at or datetime.now()
        self.status = status or TaskStatus.PENDING
        self.args = args or {}
        self.flags = flags or []
        self._id = _id or UUID(str(uuid.uuid4()))

        self.operation = operation
        self.owner_id = owner_id
        self.dataset = dataset
        self.config_version = config_version

        self.events = []
        self.commands = []

        # TODO: should probably pass in required config?
        if _config is not None:
            self._add_config(_config, config_version, self.created_at)

    def _add_config(
        self, config: ConfigModel, config_version: int, created_at: datetime
    ) -> None:
        data: Dict = json.loads(config.model_dump_json())

        self._config = Config(version=config_version, data=data, created_at=created_at)

    @property
    def config(self) -> ConfigModel:
        if self._config is not None:
            return ConfigModel.model_validate(self._config.data)

        raise ValueError(f"config is None for task {self._id}")

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
    def script_path(self) -> Path:
        if self.config is None:
            raise ValueError("config is `None`")

        script_path: Path | None = next(
            (
                script.path
                for script in self.config.scripts
                if str(self.operation) == script.model_name
            ),
            None,
        )

        if script_path is None:
            raise NoScriptWithOperation(self.operation)

        return script_path

    @property
    def filesystem_path(self) -> Path:
        if self.config is None:
            raise ValueError("config is `None`")

        filesystem_path: Path | None = next(
            (
                fs.path
                for fs in self.config.filesystems
                if fs.dataset_name == self.dataset
            ),
            None,
        )

        if filesystem_path is None:
            raise NoFileSystemWithDataset(self.dataset)

        return filesystem_path

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
                operation=operation_factory(
                    self.operation,
                    self.config,
                    self.args,
                    self.flags,
                ),
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
                if fs.path == Path(self.filesystem_path)
            ),
            None,
        )

        if dataset_name is None:
            raise ValueError(
                f"No filesystem found with path {str(self.filesystem_path)}"
            )

        return response_types.Task(
            datetime=self.created_at,
            owner_id=self.owner_id,
            model_name=self.operation,
            dataset_name=dataset_name,
            args=self.args,
            flags=self.flags,
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
