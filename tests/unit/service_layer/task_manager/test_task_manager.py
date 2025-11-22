from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from src.core.response_types import Task
from src.core.types import UUID, Operation, TaskStatus
from src.service_layer.task_manager.task_manager import TaskManager
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_http_client import FakeHTTPClient


def test_task_manager_get_all():
    dt = datetime.now()

    _, http_client, tasks = _get_setup(dt)

    task_manager = TaskManager(http_client=http_client)

    assert task_manager.get() == tasks


def test_task_manager_get_id():
    dt = datetime.now()

    _, http_client, tasks = _get_setup(dt)

    task_manager = TaskManager(http_client=http_client)

    assert task_manager.get(id=UUID("3")) == [
        task for task in tasks if task.id == UUID("3")
    ]
    assert task_manager.get(id=UUID("100")) == []


def test_task_manager_get_status():
    dt = datetime.now()

    _, http_client, tasks = _get_setup(dt)

    task_manager = TaskManager(http_client=http_client)

    assert task_manager.get(status=TaskStatus.PENDING) == [
        task for task in tasks if task.status == TaskStatus.PENDING
    ]
    assert task_manager.get(status=TaskStatus.COMPLETED) == []


def test_task_manager_get_status_and_id():
    dt = datetime.now()

    _, http_client, tasks = _get_setup(dt)

    task_manager = TaskManager(http_client=http_client)

    assert task_manager.get(id=UUID("2"), status=TaskStatus.PENDING) == [
        task for task in tasks if task.id == UUID("2")
    ]
    assert task_manager.get(id=UUID("3"), status=TaskStatus.PENDING) == []


def test_task_manager_post_task():
    dt = datetime.now()

    _, http_client, _ = _get_setup(dt)

    task_manager = TaskManager(http_client=http_client)

    task_manager.post(
        analytics_uuid_label=UUID("analytics"), dataset_uuid=UUID("dataset")
    )

    assert len(task_manager.get()) == 5


def test_task_manager_put_task():
    dt = datetime.now()

    _, http_client, _ = _get_setup(dt)

    task_manager = TaskManager(http_client=http_client)

    task_manager.put(
        id=UUID("1"),
        input_folder=Path("/"),
        owner_id=UUID("owner"),
        task_status=TaskStatus.COMPLETED,
        operation=Operation.VTC,
        dataset_name="loann_2025",
        inputs=[],
    )

    assert len(task_manager.get()) == 4
    task: Task | None = next(
        (task for task in task_manager.get() if task.id == UUID("1")), None
    )

    assert task is not None
    assert task.status == TaskStatus.COMPLETED


def _get_setup(dt: datetime) -> Tuple[PublishingUoW, FakeHTTPClient, List[Task]]:
    tasks: List[Task] = [
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
        Task(
            dataset_name="loann_2025",
            datetime=dt,
            model_name=Operation.ALICE,
            owner_id=UUID("512"),
            status=TaskStatus.FAILED,
            input_folder=Path("/"),
            inputs=[Path("/file_3.wav")],
            id=UUID("3"),
        ),
        Task(
            dataset_name="loann_2025",
            datetime=dt,
            model_name=Operation.ALICE,
            owner_id=UUID("253"),
            status=TaskStatus.RUNNING,
            input_folder=Path("/"),
            inputs=[Path("/file_4.wav")],
            id=UUID("4"),
        ),
    ]

    uow = PublishingUoW(FakeUoW())
    http_client = FakeHTTPClient(results=[tasks])

    return uow, http_client, tasks
