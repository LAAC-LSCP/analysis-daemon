from pathlib import Path

import src.domain.events as events
import src.service_layer.message_bus as message_bus
from src.service_layer.publishing_uow import PublishingUoW
from src.shared.types import UUID, Model
from tests.integration.service_layer.fakes import FakeUoW


def test_adding_returns_task_id():
    uow = PublishingUoW(FakeUoW())
    message_bus.handle(
        events.TaskCreated(
            task_id=UUID("abc"),
            owner_id=1,
            filesystem=Path("/path1"),
            script_path=Path("/script.sh"),
            model=Model.VTC,
        ),
        uow,
    )

    assert uow.tasks.get(task_id="abc") is not None


def test_commit():
    uow = PublishingUoW(FakeUoW())

    message_bus.handle(
        events.TaskCreated(
            task_id=UUID("abc"),
            owner_id=1,
            filesystem=Path("/path1"),
            script_path=Path("/script.sh"),
            model=Model.VTC,
        ),
        uow,
    )

    assert uow._uow.committed
