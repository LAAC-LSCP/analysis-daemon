from abc import abstractmethod
from typing import Generic

from src.service_layer.types import RepoType


class AbstractUoW(Generic[RepoType]):
    """
    The unit of work pattern is a wrapper around a repository, allowing for certain
    atomicity guarantees, creating a sort of transaction-like syntax for
    database interactions

    While the RDBMs is ACID-compliant, this is not guaranteed for our system as a
    whole, which includes the file system (since running a model outputs files). We
    therefore need an appropriate rollback mechanism that encompasses both database
    and file system changes during the span of a single transaction
    """

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
