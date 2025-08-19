from abc import abstractmethod

from src.adapters.repository import AbstractRepository


class AbstractUoW:
    tasks: AbstractRepository

    def __enter__(self) -> "AbstractUoW":
        return self

    def __exit__(self, *_):
        self.rollback()

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
