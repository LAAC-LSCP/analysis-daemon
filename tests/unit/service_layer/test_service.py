from datetime import datetime
from pathlib import Path

import pytest

from src.config.config import ConfigModel
from src.core.operations.operation import Operation
from src.core.response_types import Task
from src.core.types import UUID, OperationName, TaskStatus
from src.domain import commands, events
from src.domain.model import Task as ModelTask
from src.service_layer.handlers.command_handlers import get_command_handlers
from src.service_layer.handlers.event_handlers import get_event_handlers
from src.service_layer.service import Service
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_handlers import FakeHandlers
from tests.unit.service_layer.fake_http_client import FakeHTTPClient


def test_service_resumes_running_tasks(config_model: ConfigModel):
    dt = datetime.now()
    task = ModelTask(
        owner_id=UUID("123"),
        dataset="loann_2025",
        created_at=dt,
        status=TaskStatus.RUNNING,
        operation=OperationName.VTC,
        args={"input": "some-input"},
        flags=["--gpu"],
        config_version=0,
        _config=config_model,
        _id=UUID("1"),
    )

    uow = PublishingUoW(FakeUoW(config=config_model))
    handlers = FakeHandlers(uow, {})
    http_client = FakeHTTPClient(results=[])

    with uow:
        uow.tasks.save(task)

        uow.commit()

    service = Service(
        uow=uow,
        http_client=http_client,
        config=(config_model, 0),
        event_handlers=handlers.event_handlers,
        command_handlers=handlers.command_handlers,
    )

    queue = service._broker.command_queue._queue
    assert queue.qsize() == 1
    item: commands.RunTask = queue.get().item

    script_path: Path | None = next(
        (
            script.path
            for script in config_model.scripts
            if script.model_name == OperationName.VTC
        ),
        None,
    )

    assert script_path is not None
    assert item == commands.RunTask(
        task_id=UUID("1"),
        operation=Operation(
            operation=OperationName.VTC,
            script_path=script_path,
            args={"input": "some-input"},
            flags=["--gpu"],
        ),
    )


@pytest.mark.asyncio
async def test_service_puts_tasks_1_tick(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW(config=config_model))
    handlers = FakeHandlers(
        uow, {commands.CreateTask: [FakeHandlers.empty_command_handler]}
    )
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VCM,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("2"),
                ),
            ]
        ]
    )

    service = Service(
        uow=uow,
        http_client=http_client,
        config=(config_model, 0),
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
    uow = PublishingUoW(FakeUoW(config=config_model))
    handlers = FakeHandlers(
        uow,
        command_handlers={commands.CreateTask: [FakeHandlers.empty_command_handler]},
    )
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("1"),
                )
            ],
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("2"),
                ),
            ],
        ]
    )

    service = Service(
        uow=uow,
        http_client=http_client,
        config=(config_model, 0),
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
    uow = PublishingUoW(FakeUoW(config=config_model))
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("1"),
                )
            ]
        ]
    )
    handlers = FakeHandlers(
        uow,
        command_handlers=get_command_handlers(config_model, 0),
        event_handlers=get_event_handlers(http_client, config_model),
    )

    service = Service(
        uow=uow,
        http_client=http_client,
        config=(config_model, 0),
        event_handlers=handlers.event_handlers,
        command_handlers=handlers.command_handlers,
    )

    service._tick()

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 1
    assert handlers.calls[0] == (commands.CreateTask, "handle_create_task", 0)

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 2
    assert handlers.calls[1] == (events.TaskCreated, "handle_task_created", 1)

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 3
    assert handlers.calls[2] == (commands.RunTask, "handle_run_task", 2)

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 5
    assert handlers.calls[3] == (events.TaskStarted, "handle_task_started", 3)
    assert handlers.calls[4] == (events.TaskStarted, "handle_update_echolalia", 4)

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 6
    assert handlers.calls[5] == (commands.CompleteTask, "handle_complete_task", 5)

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 8
    assert handlers.calls[6] == (events.TaskCompleted, "handle_task_completed", 6)
    assert handlers.calls[7] == (events.TaskCompleted, "handle_update_echolalia", 7)


@pytest.mark.asyncio
async def test_event_storm_create_task_with_error(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW(config=config_model))

    async def handle_run_task(command: commands.RunTask, uow: PublishingUoW) -> None:
        raise Exception("Something went wrong!")

    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=OperationName.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    args={},
                    flags=[],
                    id=UUID("1"),
                )
            ]
        ]
    )

    handlers = FakeHandlers(
        uow,
        command_handlers=get_command_handlers(config_model, 0),
        event_handlers=get_event_handlers(http_client, config_model),
    )
    handlers.set_handlers_for_command(commands.RunTask, [handle_run_task])

    service = Service(
        uow=uow,
        http_client=http_client,
        config=(config_model, 0),
        event_handlers=handlers.event_handlers,
        command_handlers=handlers.command_handlers,
    )

    service._tick()

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 1
    assert handlers.calls[0] == (commands.CreateTask, "handle_create_task", 0)

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 2
    assert handlers.calls[1] == (events.TaskCreated, "handle_task_created", 1)

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 2
    assert len(handlers.exceptions) == 1
    assert handlers.exceptions[0] == (commands.RunTask, "handle_run_task", 2)

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 4
    assert handlers.calls[2] == (events.TaskFailed, "handle_task_failed", 3)
    assert handlers.calls[3] == (events.TaskFailed, "handle_update_echolalia", 4)
