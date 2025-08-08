from abc import abstractmethod
from typing import Generator

from src.adapters.repository import AbstractRepository
from src.domain.events import Event


class AbstractUoW:
    tasks: AbstractRepository

    def commit(self) -> None:
        self._commit()

    def collect_new_events(self) -> Generator[Event]:
        for task in self.tasks.seen:
            while task.events:
                yield task.events.pop(0)

    def __enter__(self) -> "AbstractUoW":
        return self

    def __exit__(self, *_):
        self.rollback()

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
