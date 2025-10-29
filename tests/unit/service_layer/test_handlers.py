from pathlib import Path

import pytest

from src.core.types import UUID, Model
from src.domain import commands
from src.service_layer.default_handlers import handle_create_task
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW


@pytest.mark.asyncio
async def test_adding_returns_task_id():
    uow = PublishingUoW(FakeUoW())
    await handle_create_task(
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

    await handle_create_task(
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
