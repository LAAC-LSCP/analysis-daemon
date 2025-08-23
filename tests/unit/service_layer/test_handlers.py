from pathlib import Path

import pytest

import src.service_layer.message_bus as message_bus
from src.domain import commands
from src.service_layer.publishing_uow import PublishingUoW
from src.shared.types import UUID, Model
from tests.integration.service_layer.fakes import FakeUoW


@pytest.mark.asyncio
async def test_adding_returns_task_id():
    uow = PublishingUoW(FakeUoW())
    await message_bus.handle(
        commands.CreateTask(
            task_id=UUID("abc"),
            owner_id=UUID("owner"),
            filesystem=Path("/path1"),
            script_path=Path("/script.sh"),
            model=Model.VTC,
        ),
        uow,
    )

    assert uow.tasks.get(task_id="abc") is not None


@pytest.mark.asyncio
async def test_commit():
    uow = PublishingUoW(FakeUoW())

    await message_bus.handle(
        commands.CreateTask(
            task_id=UUID("abc"),
            owner_id=UUID("owner"),
            filesystem=Path("/path1"),
            script_path=Path("/script.sh"),
            model=Model.VTC,
        ),
        uow,
    )

    assert uow._uow.committed
