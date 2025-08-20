from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from src.domain.model import UUID, Task


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
    def get_by_filesystem(self, filesystem_path: Path) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def save(self, task: Task) -> Task:
        raise NotImplementedError
