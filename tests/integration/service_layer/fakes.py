from typing import Optional

from src.adapters.repository import AbstractRepository
from src.adapters.tracking_repository import TrackingRepository
from src.config.config import ConfigModel
from src.domain.commands import Command
from src.domain.events import Event
from src.service_layer.unit_of_work.uow import AbstractUoW
from tests.unit.service_layer.fake_repository import FakeRepository


class Event1(Event):
    pass


class Event2(Event):
    pass


class Command1(Command):
    pass


class Command2(Command):
    pass


class FakeUoW(AbstractUoW[TrackingRepository[AbstractRepository]]):
    committed: bool
    _tracking: bool

    # Include config here to account for the fact that we don't
    # explicitly run config saving beforehand
    def __init__(
        self, config: Optional[ConfigModel] = None, tracking: Optional[bool] = None
    ):
        self._tracking = tracking or True
        self.tasks = TrackingRepository(FakeRepository(config=config))

        if self._tracking:
            self.tasks = TrackingRepository(self.tasks)

        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
