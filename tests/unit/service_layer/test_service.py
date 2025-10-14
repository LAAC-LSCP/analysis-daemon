from datetime import datetime

import pytest

from src.config.config import ConfigModel
from src.core.response_types import Task
from src.core.types import UUID, Model, TaskStatus
from src.domain import commands
from src.service_layer.service import Service
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_handlers import FakeHandlers
from tests.unit.service_layer.fake_http_client import FakeHTTPClient


@pytest.mark.asyncio
async def test_service_puts_tasks_1_tick(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(uow, {commands.CreateTask: ["result_1", "result_2"]})
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.UNKNOWN,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("2"),
                ),
            ]
        ]
    )

    service = Service(
        uow=uow,
        http_client=http_client,
        config=config_model,
        event_handlers=handlers.event_handlers,
        command_handlers=handlers.command_handlers,
    )

    await service._tick()

    assert len(service._broker.queued_commands) == 2


@pytest.mark.asyncio
async def test_service_create_tasks_2_ticks(config_model: ConfigModel):
    """
    Simulates a different response coming in later
    Where user with `owner_id==UUID(123)` decided to also calculate-aclew

    Checks that the tasks are properly loaded, not duplicated
    """
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(uow, {commands.CreateTask: ["result_1", "result_2"]})
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                )
            ],
            [
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("2"),
                ),
            ],
        ]
    )

    service = Service(
        uow=uow,
        http_client=http_client,
        config=config_model,
        event_handlers=handlers.event_handlers,
        command_handlers=handlers.command_handlers,
    )

    await service._tick()

    assert len(service._broker.queued_commands) == 1

    await service._tick()

    assert len(service._broker.queued_commands) == 2
