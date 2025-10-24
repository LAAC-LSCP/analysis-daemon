import platform
from datetime import datetime

import pytest

from src.core import response_types
from src.core.types import UUID, Model, TaskStatus
from src.service_layer.http_client import HTTPClient
from tests.e2e.conftest import TEST_SERVER_DOMAIN, TEST_SERVER_PORT


def test_http_client_get_all_tasks(http_client: HTTPClient):
    tasks = http_client.get_all_tasks()

    assert tasks == [
        response_types.Task(
            datetime=datetime(year=2021, month=1, day=1),
            owner_id=UUID("1001"),
            model_name=Model.VTC,
            dataset_name="loann_2025",
            status=TaskStatus.PENDING,
            id=UUID("1"),
        ),
        response_types.Task(
            datetime=datetime(year=2022, month=1, day=1),
            owner_id=UUID("1002"),
            model_name=Model.VTC,
            dataset_name="loann_2025",
            status=TaskStatus.RUNNING,
            id=UUID("2"),
        ),
    ]


def test_http_client_get_by_id(http_client: HTTPClient):
    task = http_client.get_task_by_id(UUID("1"))

    assert task == response_types.Task(
        datetime=datetime(year=2021, month=1, day=1),
        owner_id=UUID("1001"),
        model_name=Model.VTC,
        dataset_name="loann_2025",
        status=TaskStatus.PENDING,
        id=UUID("1"),
    )


def test_http_client_get_by_status(http_client: HTTPClient):
    tasks = http_client.get_all_tasks_with_status(TaskStatus.RUNNING)

    assert tasks == [
        response_types.Task(
            datetime=datetime(year=2022, month=1, day=1),
            owner_id=UUID("1002"),
            model_name=Model.VTC,
            dataset_name="loann_2025",
            status=TaskStatus.RUNNING,
            id=UUID("2"),
        ),
    ]


@pytest.mark.asyncio
async def test_http_client_put_task(http_client: HTTPClient):
    await http_client.put_task(
        response_types.Task(
            datetime=datetime.now(),
            owner_id=UUID("1001"),
            model_name=Model.VTC,
            dataset_name="loann_2025",
            status=TaskStatus.RUNNING,
            id=UUID("3"),
        )
    )

    tasks = http_client.get_all_tasks()

    assert len([task for task in tasks if task.id == UUID("3")]) == 1

    http_client.delete_task(UUID("3"))


# TODO: Test retries too


@pytest.fixture(scope="module")
def http_client() -> HTTPClient:
    if platform.system() == "Darwin":
        # TODO: Fix socket creation timing out
        pytest.skip(
            "Skipping E2E tests on MacOS runner due to networking restrictions",
        )

    return HTTPClient(
        remote_api_url=f"http://{TEST_SERVER_DOMAIN}:{TEST_SERVER_PORT}",
        client_id="test_id",
        client_secret="test_secret",
        timeout_s=100_000,  # NOTE: Adjust for debugging, keep low for test runs
    )
