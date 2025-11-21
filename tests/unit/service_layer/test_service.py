from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

from src.config.config import ConfigModel
from src.core.response_types import Task
from src.core.types import UUID, Operation, TaskStatus
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
        operation=Operation.VTC,
        input_folder=Path("/my_input_folder"),
        input_files=[
            Path("/my_input_folder/file_1.wav"),
            Path("/my_input_folder/file_2.wav"),
        ],
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
    item: commands.RunTask = queue.get().item
    assert item == commands.RunTask(
        task_id=UUID("1"),
        dataset="loann_2025",
        operation=Operation.VTC,
        input_folder=Path("/my_input_folder"),
        echolalia_folder=config_model.echolalia_folder,
        input_files=[
            Path("/my_input_folder/file_1.wav"),
            Path("/my_input_folder/file_2.wav"),
        ],
    )


@pytest.mark.asyncio
async def test_service_puts_tasks_1_tick(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    handlers = FakeHandlers(
        uow, {commands.CreateTask: [FakeHandlers.empty_command_handler]}
    )
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    input_folder=Path("/"),
                    inputs=[Path("/file_1.wav"), Path("/file_2.wav")],
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.ALICE,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    input_folder=Path("/"),
                    inputs=[Path("/file_1.wav"), Path("/file_2.wav")],
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
    Where user with `owner_id==UUID(123)` decided to also do VTC

    Checks that the tasks are properly loaded, not duplicated
    """
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
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
                    model_name=Operation.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    input_folder=Path("/"),
                    inputs=[Path("/file_1.wav"), Path("/file_2.wav")],
                    id=UUID("1"),
                )
            ],
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    input_folder=Path("/"),
                    inputs=[Path("/file_1.wav"), Path("/file_2.wav")],
                    id=UUID("1"),
                ),
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    input_folder=Path("/"),
                    inputs=[Path("/file_3.wav"), Path("/file_4.wav")],
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
async def test_event_storm_create_task(config_model: ConfigModel, config_path: Path):
    """Test event storming of a creation task"""
    filesystem = config_path.parent
    example_inputs = (
        filesystem / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )
    input_1 = example_inputs / "empty_wav.wav"
    input_2 = example_inputs / "folder_1" / "folder_3" / "empty_wav_1_3_1.wav"

    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("a87bac8b-21a1-4a46-b812-392be4e360e5"),
                    status=TaskStatus.PENDING,
                    input_folder=example_inputs,
                    inputs=[input_1, input_2],
                    id=UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be"),
                )
            ]
        ]
    )
    handlers = FakeHandlers(
        uow,
        command_handlers=get_command_handlers(config_model),
        event_handlers=get_event_handlers(http_client),
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
    assert handlers.calls[0]["type"] == commands.CreateTask
    assert handlers.calls[0]["handler_name"] == "handle_create_task"

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 2
    assert handlers.calls[1]["type"] == events.TaskCreated
    assert handlers.calls[1]["handler_name"] == "handle_task_created"

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 3
    assert handlers.calls[2]["type"] == commands.RunTask
    assert handlers.calls[2]["handler_name"] == "handle_run_task"

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 5
    assert handlers.calls[3]["type"] == events.TaskStarted
    assert handlers.calls[3]["handler_name"] == "handle_task_started"
    assert handlers.calls[4]["type"] == events.TaskStarted
    assert handlers.calls[4]["handler_name"] == "handle_update_echolalia"

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 6
    assert handlers.calls[5]["type"] == commands.CheckTask
    assert handlers.calls[5]["handler_name"] == "handle_check_task"

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 7
    assert handlers.calls[6]["type"] == commands.CompleteTask
    assert handlers.calls[6]["handler_name"] == "handle_complete_task"

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 9
    assert handlers.calls[7]["type"] == events.TaskCompleted
    assert handlers.calls[7]["handler_name"] == "handle_task_completed"
    assert handlers.calls[8]["type"] == events.TaskCompleted
    assert handlers.calls[8]["handler_name"] == "handle_update_echolalia"

    # Nothing left over
    await service._broker.event_queue._tick()
    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 9


@pytest.mark.asyncio
async def test_event_storm_two_tasks(config_model: ConfigModel, config_path: Path):
    """Test event storming of a creation task"""
    filesystem = config_path.parent
    example_inputs = (
        filesystem / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )
    input_1 = example_inputs / "empty_wav.wav"
    input_2 = example_inputs / "folder_1" / "folder_3" / "empty_wav_1_3_1.wav"
    input_3 = example_inputs / "folder_1" / "folder_3" / "empty_wav_1_3_2.wav"

    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())
    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("a87bac8b-21a1-4a46-b812-392be4e360e5"),
                    status=TaskStatus.PENDING,
                    input_folder=example_inputs,
                    inputs=[input_1, input_2],
                    id=UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be"),
                ),
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("e24afcc6-edec-47a1-95ee-bad989acf406"),
                    status=TaskStatus.PENDING,
                    input_folder=example_inputs,
                    inputs=[input_3],
                    id=UUID("cae99af0-1e73-4446-9904-733399b8e1a1"),
                ),
            ]
        ]
    )
    handlers = FakeHandlers(
        uow,
        command_handlers=get_command_handlers(config_model),
        event_handlers=get_event_handlers(http_client),
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

    assert len(handlers.calls) == 2
    counts_1 = Counter(
        [
            handlers.calls[0]["type"],
            handlers.calls[1]["type"],
            handlers.calls[0]["message"].task_id,
            handlers.calls[1]["message"].task_id,
        ]
    )
    assert counts_1[UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be")] == 1
    assert counts_1[UUID("cae99af0-1e73-4446-9904-733399b8e1a1")] == 1
    assert counts_1[commands.CreateTask] == 2

    await service._broker.event_queue._tick()

    assert len(handlers.calls) == 4

    counts_2 = Counter(
        [
            handlers.calls[2]["type"],
            handlers.calls[3]["type"],
            handlers.calls[2]["message"].task_id,
            handlers.calls[3]["message"].task_id,
        ]
    )
    assert counts_2[UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be")] == 1
    assert counts_2[UUID("cae99af0-1e73-4446-9904-733399b8e1a1")] == 1
    assert counts_2[events.TaskCreated] == 2

    await service._broker.command_queue._tick()

    assert len(handlers.calls) == 6

    counts_3 = Counter(
        [
            handlers.calls[4]["type"],
            handlers.calls[5]["type"],
            handlers.calls[4]["message"].task_id,
            handlers.calls[5]["message"].task_id,
        ]
    )
    assert counts_3[UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be")] == 1
    assert counts_3[UUID("cae99af0-1e73-4446-9904-733399b8e1a1")] == 1
    assert counts_3[commands.RunTask] == 2

    await service._broker.event_queue._tick()

    assert len(handlers.calls) == 10
    counts_4 = Counter(
        [
            handlers.calls[6]["handler_name"],
            handlers.calls[7]["handler_name"],
            handlers.calls[8]["handler_name"],
            handlers.calls[9]["handler_name"],
            handlers.calls[6]["message"].task_id,
            handlers.calls[7]["message"].task_id,
            handlers.calls[8]["message"].task_id,
            handlers.calls[9]["message"].task_id,
        ]
    )
    assert counts_4["handle_update_echolalia"] == 2
    assert counts_4["handle_task_started"] == 2
    assert counts_4[UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be")] == 2
    assert counts_4[UUID("cae99af0-1e73-4446-9904-733399b8e1a1")] == 2

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 12
    counts_5 = Counter(
        [
            handlers.calls[10]["handler_name"],
            handlers.calls[11]["handler_name"],
            handlers.calls[10]["message"].task_id,
            handlers.calls[11]["message"].task_id,
        ]
    )
    assert counts_5["handle_check_task"] == 2
    assert counts_5["2920bfb0-8a16-478d-8654-aa7a7e0a23be"] == 1
    assert counts_5["cae99af0-1e73-4446-9904-733399b8e1a1"] == 1

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 14
    counts_6 = Counter(
        [
            handlers.calls[12]["handler_name"],
            handlers.calls[13]["handler_name"],
            handlers.calls[12]["message"].task_id,
            handlers.calls[13]["message"].task_id,
        ]
    )
    assert counts_6["handle_complete_task"] == 2
    assert counts_6[UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be")] == 1
    assert counts_6[UUID("cae99af0-1e73-4446-9904-733399b8e1a1")] == 1

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 18
    counts_7 = Counter(
        [
            handlers.calls[14]["handler_name"],
            handlers.calls[15]["handler_name"],
            handlers.calls[16]["handler_name"],
            handlers.calls[17]["handler_name"],
            handlers.calls[14]["message"].task_id,
            handlers.calls[15]["message"].task_id,
            handlers.calls[16]["message"].task_id,
            handlers.calls[17]["message"].task_id,
        ]
    )
    assert counts_7["handle_update_echolalia"] == 2
    assert counts_7["handle_task_completed"] == 2
    assert counts_7[UUID("2920bfb0-8a16-478d-8654-aa7a7e0a23be")] == 2
    assert counts_7[UUID("cae99af0-1e73-4446-9904-733399b8e1a1")] == 2

    # Nothing left over
    await service._broker.event_queue._tick()
    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 18


@pytest.mark.asyncio
async def test_event_storm_create_task_with_error(config_model: ConfigModel):
    dt = datetime.now()
    uow = PublishingUoW(FakeUoW())

    async def handle_run_task(command: commands.RunTask, uow: PublishingUoW) -> None:
        raise Exception("Something went wrong!")

    http_client = FakeHTTPClient(
        results=[
            [
                Task(
                    dataset_name="loann_2025",
                    datetime=dt,
                    model_name=Operation.VTC,
                    owner_id=UUID("123"),
                    status=TaskStatus.PENDING,
                    input_folder=Path("/"),
                    inputs=[Path("/file_1.wav"), Path("/file_2.wav")],
                    id=UUID("1"),
                )
            ]
        ]
    )

    handlers = FakeHandlers(
        uow,
        command_handlers=get_command_handlers(config_model),
        event_handlers=get_event_handlers(http_client),
    )
    handlers.set_handlers_for_command(commands.RunTask, [handle_run_task])

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
    assert handlers.calls[0]["type"] == commands.CreateTask
    assert handlers.calls[0]["handler_name"] == "handle_create_task"

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 2
    assert handlers.calls[1]["type"] == events.TaskCreated
    assert handlers.calls[1]["handler_name"] == "handle_task_created"

    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 2
    assert len(handlers.exceptions) == 1
    assert handlers.exceptions[0]["type"] == commands.RunTask
    assert handlers.exceptions[0]["handler_name"] == "handle_run_task"

    await service._broker.event_queue._tick()
    assert len(handlers.calls) == 4
    assert handlers.calls[2]["type"] == events.TaskFailed
    assert handlers.calls[2]["handler_name"] == "handle_task_failed"
    assert handlers.calls[3]["type"] == events.TaskFailed
    assert handlers.calls[3]["handler_name"] == "handle_update_echolalia"

    # Nothing left over
    await service._broker.event_queue._tick()
    await service._broker.command_queue._tick()
    assert len(handlers.calls) == 4
    assert len(handlers.exceptions) == 1
