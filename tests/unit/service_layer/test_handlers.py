import pytest

from src.config.config import ConfigModel
from src.core.operations.operation import operation_factory
from src.core.types import UUID, OperationName
from src.domain import commands
from src.service_layer.handlers.command_handlers import get_handle_create_task
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW


@pytest.mark.asyncio
async def test_adding_returns_task_id(config_model: ConfigModel):
    uow = PublishingUoW(FakeUoW(config=config_model))
    await get_handle_create_task(config_model, 0)(
        commands.CreateTask(
            task_id=UUID("abc"),
            owner_id=UUID("owner"),
            dataset="loann_2025",
            operation=operation_factory(OperationName.VTC, config_model),
        ),
        uow,
    )

    assert uow.tasks.get(task_id=UUID("abc")) is not None


@pytest.mark.asyncio
async def test_commit(config_model: ConfigModel):
    uow = PublishingUoW(FakeUoW(config=config_model))

    await get_handle_create_task(config_model, 0)(
        commands.CreateTask(
            task_id=UUID("abc"),
            owner_id=UUID("owner"),
            dataset="loann_2025",
            operation=operation_factory(OperationName.VTC, config_model),
        ),
        uow,
    )

    # TODO: fix this sudden typing problem?
    assert uow._uow.committed  # type: ignore
