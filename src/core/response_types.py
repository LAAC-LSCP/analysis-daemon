from dataclasses import dataclass
from datetime import datetime
from typing import List

from src.shared.types import UUID, Model

type EcholaliaResponse = List["Task"]


@dataclass
class Task:
    datetime: datetime
    owner_id: UUID
    model_name: Model
    dataset_name: str
    script_name: str

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return (
            self.datetime == other.datetime
            and self.owner_id == other.owner_id
            and self.model_name == other.model_name
            and self.dataset_name == other.dataset_name
            and self.script_name == other.script_name
        )

    def __hash__(self):
        return hash(
            (
                self.datetime,
                self.owner_id,
                self.model_name,
                self.dataset_name,
                self.script_name,
            )
        )
