from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.model import Task


class AbstractRepository(ABC):
    """
    An abstract base class for a task repository
    """

    @abstractmethod
    def get(self, task_id: int) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_owner(self, owner_id: int) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Task]:
        raise NotImplementedError

    @abstractmethod
    def save(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def delete(self, task_id: int) -> None:
        raise NotImplementedError
