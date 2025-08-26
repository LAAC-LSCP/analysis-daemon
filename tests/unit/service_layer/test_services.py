from pathlib import Path

from src.service_layer.services import add_task
from src.shared.types import UUID
from tests.integration.service_layer.fakes import FakeUoW


def test_adding_returns_task_id():
    uow = FakeUoW()

    result = add_task(
        owner_id=1,
        filesystem=Path("/path1"),
        uow=uow,
    )

    assert result == UUID("e3e70682-c209-4cac-a29f-6fbed82c07cd")


def test_commit():
    uow = FakeUoW()

    add_task(owner_id=1, filesystem=Path("."), uow=uow)

    assert uow.committed
