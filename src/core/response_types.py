"""
This file contains the different response formats/types expected
from the Echolalia-owned endpoints
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, TypedDict

from src.core.types import UUID, Operation, TaskStatus
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
    model_name: Operation
    dataset_name: str
    status: TaskStatus
    id: UUID

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

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
            model_name=Operation(data["model_name"]),
            dataset_name=data["dataset_name"],
            status=TaskStatus(data["status"]),
            id=UUID(data["id"]),
        )

    # TODO: pass in not config, but uow to get the config version
    def to_model_type_task(self) -> "model.Task":
        return model.Task(
            owner_id=self.owner_id,
            dataset=self.dataset_name,
            created_at=self.datetime,
            status=self.status,
            operation=self.model_name,
            _id=self.id,
            config_version=0,  # TODO: need to change this
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
