from datetime import datetime
from pathlib import Path

import pytest

from src.config.config import ConfigModel
from src.core.response_types import Task
from src.core.types import UUID, Model, TaskStatus
from src.domain import commands, events
from src.domain.model import Task as ModelTask
from src.service_layer.service import Service
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_handlers import ExceptionResults, FakeHandlers
from tests.unit.service_layer.fake_http_client import FakeHTTPClient


def test_service_resumes_running_tasks(config_model: ConfigModel):
    dt = datetime.now()
    task = ModelTask(
        owner_id=UUID("123"),
        filesystem=Path("dataset"),
        script_path=Path("script"),
        created_at=dt,
        status=TaskStatus.RUNNING,
        model=Model.VTC,
        _id=UUID("1"),
    )

    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(uow, {})
    http_client = FakeHTTPClient(results=[])

    with uow:
        uow.tasks.save(task)

        uow.commit()

    service = Service(
        uow=uow,
        http_client=http_client,
        config=config_model,
        event_handlers=handlers.event_handlers,
        command_handlers=handlers.command_handlers,
    )

    queue = service._broker.command_queue._queue
    assert queue.qsize() == 1
    assert queue.get().item == commands.RunTask(
        task_id=UUID("1"), filesystem_path=Path("dataset"), script_path=Path("script")
    )


@pytest.mark.asyncio
async def test_service_puts_tasks_1_tick(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(uow, {commands.CreateTask: ["result_1", "result_2"]})
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Model.VCM,
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

    service._tick()

    assert service._broker.command_queue._queue.qsize() == 2


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
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                )
            ],
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann_2025",
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

    service._tick()

    assert service._broker.command_queue._queue.qsize() == 1

    service._tick()

    assert service._broker.command_queue._queue.qsize() == 2


@pytest.mark.asyncio
async def test_event_storm_create_task(config_model: ConfigModel):
    """Test event storming of a creation task"""
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(
        uow,
        {
            commands.CreateTask: ["created"],
            commands.RunTask: ["ran"],
            commands.CompleteTask: ["completed"],
        },
    )
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                )
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

    service._tick()

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 1
    assert handlers.calls[0] == (commands.CreateTask, "created")

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 2
    assert handlers.calls[1] == (events.TaskCreated, None)

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 3
    assert handlers.calls[2] == (commands.RunTask, "ran")

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 4
    assert handlers.calls[3] == (events.TaskStarted, None)

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 5
    assert handlers.calls[4] == (commands.CompleteTask, "completed")

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 6
    assert handlers.calls[5] == (events.TaskCompleted, None)


@pytest.mark.asyncio
async def test_event_storm_create_task_with_error(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(
        uow,
        {
            commands.CreateTask: ["created"],
            commands.RunTask: ["ran"],
            commands.CompleteTask: ["completed"],
        },
    )

    async def handle_run_task(command: commands.RunTask, uow: PublishingUoW) -> None:
        raise Exception("Something went wrong!")

    handlers.set_command_handler(commands.RunTask, [handle_run_task])

    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Model.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    id=UUID("1"),
                )
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

    service._tick()

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 1
    assert handlers.calls[0] == (commands.CreateTask, "created")

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 2
    assert handlers.calls[1] == (events.TaskCreated, None)

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 3
    assert handlers.calls[2] == (commands.RunTask, ExceptionResults.TASK_FAILURE)

    # At this point the failure event has been added

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 4
    assert handlers.calls[3] == (events.TaskFailed, None)
