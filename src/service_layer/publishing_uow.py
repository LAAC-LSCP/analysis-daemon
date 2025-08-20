from typing import Generator

from src.adapters.tracking_repository import TrackingRepository
from src.domain.commands import Command
from src.domain.events import Event
from src.service_layer.uow import AbstractUoW


class PublishingUoW(AbstractUoW[TrackingRepository]):
    """
    Decorator for unit of work to allow it to publish events
    """

    _uow: AbstractUoW[TrackingRepository]

    @property
    def tasks(self) -> TrackingRepository:
        return self._uow.tasks

    @tasks.setter
    def tasks(self, value: TrackingRepository) -> None:
        self._uow.tasks = value

    def __init__(self, uow: AbstractUoW[TrackingRepository]):
        self._uow = uow

    def __enter__(self):
        self._uow.__enter__()

    def __exit__(self, *args):
        self._uow.__exit__(*args)

    def rollback(self):
        self._uow.rollback()

    def commit(self) -> None:
        self._uow.commit()

    def collect_new_events(self) -> Generator[Event]:
        for task in self._uow.tasks.seen:
            while task.events:
                yield task.events.pop(0)

    def collect_new_commands(self) -> Generator[Command]:
        for task in self._uow.tasks.seen:
            while task.commands:
                yield task.commands.pop(0)
