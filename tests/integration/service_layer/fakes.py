from src.domain import commands
from src.service_layer.uow import AbstractUoW
from tests.unit.service_layer.fakes import FakeRepository


class Command1(commands.Command):
    pass


class Command2(commands.Command):
    pass


class FakeUoW(AbstractUoW):
    committed: bool

    def __init__(self):
        self.tasks = FakeRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
