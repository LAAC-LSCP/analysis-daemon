from abc import abstractmethod
from typing import Generic

from src.service_layer import RepoType


class AbstractUoW(Generic[RepoType]):
    tasks: RepoType

    def __enter__(self) -> "AbstractUoW[RepoType]":
        return self

    def __exit__(self, *_):
        self.rollback()

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
