import pytest

from src.config.config import ConfigModel
from src.core.types import UUID, Model
from src.domain import commands
from src.service_layer.handlers.command_handlers import handle_create_task
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW


@pytest.mark.asyncio
async def test_adding_returns_task_id(config_model: ConfigModel):
    uow = PublishingUoW(FakeUoW())
    await handle_create_task(
        commands.CreateTask(
            task_id=UUID("abc"),
            owner_id=UUID("owner"),
            dataset="loann_2025",
            model=Model.VTC,
            config=config_model,
        ),
        uow,
    )

    assert uow.tasks.get(task_id=UUID("abc")) is not None


@pytest.mark.asyncio
async def test_commit(config_model: ConfigModel):
    uow = PublishingUoW(FakeUoW())

    await handle_create_task(
        commands.CreateTask(
            task_id=UUID("abc"),
            owner_id=UUID("owner"),
            dataset="loann_2025",
            model=Model.VTC,
            config=config_model,
        ),
        uow,
    )

    # TODO: fix this sudden typing problem?
    assert uow._uow.committed  # type: ignore
