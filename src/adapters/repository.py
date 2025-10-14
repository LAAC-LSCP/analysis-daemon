"""
The repository mapping relies on the SQLAlchemy-ORM's internal mapping mechanism
and creates an even simpler interface within our domain (e.g., tasks)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Set

from src.core.types import UUID, TaskStatus
from src.domain.model import Task


class AbstractRepository(ABC):
    """
    An abstract base class for a task repository
    """

    @abstractmethod
    def get(self, task_id: UUID) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_owner(self, owner_id: UUID) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_owners(self, owner_ids: Set[UUID]) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_status(self, status: TaskStatus) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_filesystem(self, filesystem_path: Path) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def save(self, task: Task) -> Task:
        raise NotImplementedError
