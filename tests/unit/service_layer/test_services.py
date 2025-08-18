from pathlib import Path

from src.service_layer.services import add_task
from src.shared.types import UUID
from tests.unit.service_layer.fakes import (
    FakeRepository,
    FakeSession,
)


def test_adding_returns_task_id():
    repo = FakeRepository(seed=0)

    result = add_task(
        owner_id=1, filesystem=Path("/path1"), repo=repo, session=FakeSession()
    )

    assert result == UUID("e3e70682-c209-4cac-a29f-6fbed82c07cd")


def test_commit():
    repo = FakeRepository([])
    session = FakeSession()

    add_task(owner_id=1, filesystem=Path("."), repo=repo, session=session)

    assert session.committed
