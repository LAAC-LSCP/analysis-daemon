from datetime import datetime

import pytest

from src.config.config import ConfigModel
from src.core.response_types import Task
from src.core.service import Service
from src.domain import commands
from src.service_layer.publishing_uow import PublishingUoW
from src.shared.types import UUID, Model, TaskStatus
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.core.fake_handlers import FakeHandlers
from tests.unit.core.fake_http_client import FakeHTTPClient


@pytest.mark.asyncio
async def test_service_create_tasks_1_tick(config_model: ConfigModel):
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
                    script_name="run-model",
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    script_name="calculate-aclew",
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

    assert len(handlers.calls) == 2
    assert handlers.calls[0] == (commands.CreateTask, "result_1")
    assert handlers.calls[1] == (commands.CreateTask, "result_2")


@pytest.mark.asyncio
async def test_service_create_tasks_2_ticks(config_model: ConfigModel):
    """
    Simulates a different response coming in later
    Where user with `owner_id==UUID(123)` decided to also calculate-aclew

    Checks that the handlers are only called once, even though
    the response will give us two tasks (one has already been handled by the
    time we get two)
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
                    script_name="run-model",
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
                    script_name="run-model",
                    status=TaskStatus.PENDING,
                    id=UUID("2"),
                ),
                Task(
                    dataset_name="loann-2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    script_name="calculate-aclew",
                    status=TaskStatus.PENDING,
                    id=UUID("3"),
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

    assert len(handlers.calls) == 1
    assert handlers.calls[0] == (commands.CreateTask, "result_1")

    await service._tick()

    assert len(handlers.calls) == 2
    assert handlers.calls[1] == (commands.CreateTask, "result_2")
