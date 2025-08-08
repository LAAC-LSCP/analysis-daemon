from abc import abstractmethod

import src.service_layer.message_bus as message_bus
from src.adapters.repository import AbstractRepository


class AbstractUoW:
    tasks: AbstractRepository

    def commit(self) -> None:
        self._commit()
        self.publish_events()

    def publish_events(self) -> None:
        for task in self.tasks.seen:
            while task.events:
                event = task.events.pop(0)
                message_bus.handle(event)

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
