"""
This file contains the different response formats/types expected
from the Echolalia-owned endpoints
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from src.config.config import ConfigModel, FileSystemConfig
from src.core.types import UUID, Model, TaskStatus
from src.domain import model

type Tasks = List["Task"]
type Statuses = List["Status"]


class AuthResponse(TypedDict):
    access_token: str
    expires_in: int
    token_type: str


class Status(TypedDict):
    pk_nc_analysis_status_type: int
    label: str
    uid_label: TaskStatus
    modified: datetime
    created: datetime


class PostPayload(TypedDict):
    """
    The 'post' endpoint is quite restricted for security reasons
    and therefore has a kind of odd payload, not a partial task
    as you might expect
    """

    analytics_uid_label: str
    uid_dataset: str
    kc_sub: str
    estimated_duration: int


@dataclass
class Task:
    datetime: datetime
    owner_id: UUID
    model_name: Model
    dataset_name: str
    status: TaskStatus
    id: UUID

    # TODO: this is quite hacky. I probably want to remove this
    # later when I write better task-loading logic
    # in fact it's much preferred to work with the id alone e.g., for replacing tasks
    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return (
            self.owner_id == other.owner_id
            and self.model_name == other.model_name
            and self.dataset_name == other.dataset_name
        )

    def __hash__(self):
        return hash(
            (
                self.owner_id,
                self.model_name,
                self.dataset_name,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime.isoformat(),
            "owner_id": str(self.owner_id),
            "model_name": (
                self.model_name.value
                if hasattr(self.model_name, "value")
                else str(self.model_name)
            ),
            "dataset_name": self.dataset_name,
            "status": (
                self.status.value if hasattr(self.status, "value") else str(self.status)
            ),
            "id": str(self.id),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Task":
        return Task(
            datetime=datetime.fromisoformat(data["datetime"]),
            owner_id=UUID(data["owner_id"]),
            model_name=Model(data["model_name"]),
            dataset_name=data["dataset_name"],
            status=TaskStatus(data["status"]),
            id=UUID(data["id"]),
        )

    def to_model_type_task(self, config: ConfigModel) -> "model.Task":
        filesystem_config: FileSystemConfig | None = next(
            (fs for fs in config.filesystems if fs.dataset_name == self.dataset_name),
            None,
        )

        if filesystem_config is None:
            raise ValueError(f"No filesystem found for dataset {self.dataset_name}")

        # TODO: clear symptom that the configuration isn't quite set up right... But
        # too early to go fix this, more important things to do.
        script_path: Path | None = next(
            (
                script.script_path
                for script in filesystem_config.scripts
                if script.model_name == self.model_name
            ),
            None,
        )

        if script_path is None:
            raise ValueError(
                f"No script found in dataset {self.dataset_name} \
                with model {self.model_name}"
            )

        return model.Task(
            owner_id=self.owner_id,
            filesystem=filesystem_config.path,
            created_at=self.datetime,
            status=self.status,
            script_path=script_path,
            model=self.model_name,
            _id=self.id,
        )

    def __str__(self) -> str:
        return (
            f"Task {self.id}\n"
            f"  Model: {self.model_name}\n"
            f"  Dataset: {self.dataset_name}\n"
            f"  Status: {self.status}\n"
            f"  Owner: {self.owner_id}\n"
            f"  Created: {self.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )
