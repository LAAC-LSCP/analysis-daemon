"""
This file contains the different response formats/types expected
from the Echolalia-owned endpoints
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, TypedDict

from src.shared.types import UUID, Model, TaskStatus

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
