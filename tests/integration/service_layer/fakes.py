from src.service_layer.uow import AbstractUoW
from tests.unit.service_layer.fakes import FakeRepository


class FakeUoW(AbstractUoW):
    committed: bool

    def __init__(self):
        self.tasks = FakeRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
