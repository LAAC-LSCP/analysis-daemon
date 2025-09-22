from typing import Mapping, Optional

import httpx
import requests
from tenacity import retry, wait_fixed

import src.core.response_types as response_types
from src.domain.model import Task as DomainTask
from src.shared.types import UUID, Model, TaskStatus

Headers = Mapping[str, str]


class HTTPClient:
    """
    The HTTPClient calls the Echolalia endpoint to get tasks. It furthermore
    allows updating the server's task statuses

    TODO: Instead of throwing errors on GET just retry and log
    """

    _retry_time_s: int = 10
    _timeout_s: int

    _remote_api_url: str
    _access_token: str

    def __init__(
        self,
        remote_api_url: str,
        client_id: str,
        client_secret: str,
        timeout_s: Optional[int] = 10,
        retry_time_s: Optional[int] = 10,
    ):
        self._timeout_s = timeout_s or 10
        self._retry_time_s = retry_time_s or 10

        self._remote_api_url = remote_api_url.rstrip("/")

        self._access_token = self._get_access_token(client_id, client_secret)

    @property
    def headers(self) -> Headers:
        return {
            "Authorization": f"Bearer {self._access_token}",
        }

    def _get_access_token(self, client_id: str, client_secret: str) -> str:
        uri: str = self._remote_api_url + "/api/auth/login-service"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        response = requests.post(uri, data=payload, timeout=self._timeout_s)
        response.raise_for_status()

        # TODO: need to double check this is the right field
        return response.json()["access_token"]

    def get_all_tasks(self) -> response_types.EcholaliaResponse:
        uri: str = self._remote_api_url + "/api/analytics/tasks/"

        try:
            response = requests.get(uri, headers=self.headers, timeout=self._timeout_s)
            response.raise_for_status()
            data = response.json()

            return [response_types.Task.from_dict(task) for task in data]
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to fetch tasks from {self._remote_api_url}: {exc}"
            ) from exc

    def get_all_tasks_with_status(
        self, status: TaskStatus
    ) -> response_types.EcholaliaResponse:
        # TODO: Collides with the tasks_by_id endpoint, could be a problem
        # if we add new types of status
        uri: str = self._remote_api_url + f"/api/analytics/tasks/{status}"

        try:
            response = requests.get(uri, headers=self.headers, timeout=self._timeout_s)
            response.raise_for_status()
            data = response.json()

            return [response_types.Task.from_dict(task) for task in data]
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to fetch tasks from {self._remote_api_url}: {exc}"
            ) from exc

    def get_task_by_id(self, id: UUID) -> response_types.Task:
        uri: str = self._remote_api_url + f"/api/analytics/tasks/{id}"

        try:
            response = requests.get(uri, headers=self.headers, timeout=self._timeout_s)
            response.raise_for_status()
            data = response.json()

            return response_types.Task.from_dict(data)
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to fetch task with UUID {id} from \
                {self._remote_api_url}: {exc}"
            ) from exc

    # Not officially part of the Echolalia API, but useful in our test environment
    def delete_task(self, id: UUID) -> None:
        uri: str = self._remote_api_url + f"/api/analytics/tasks/{id}"

        try:
            response = requests.delete(
                uri, headers=self.headers, timeout=self._timeout_s
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to delete task with UUID {id} from {self._remote_api_url}: \
                    {exc}"
            ) from exc

    @retry(
        reraise=True,
        wait=wait_fixed(_retry_time_s),
    )
    async def put_task(self, task: DomainTask) -> None:
        uri: str = self._remote_api_url + f"/api/analytics/tasks/{task._id}"

        # TODO: I think it's useful to change the namings later on
        # in how we define tasks in our domain
        # also some helpers that convert our domain- and request-like tasks
        # might be useful
        request_task = response_types.Task(
            datetime=task.created_at,
            owner_id=task.owner_id,
            model_name=task.model or Model.UNKNOWN,
            dataset_name=str(task.filesystem),
            script_name=str(task.script_path),
            status=task.status,
            id=task._id,
        )

        payload: Mapping[str, str] = request_task.to_dict()

        # While getting should block the scheduler's main loop, as scheduling depends
        # on retrieving tasks updates and retries should not
        async with httpx.AsyncClient() as client:
            response = await client.put(
                uri, headers=self.headers, json=payload, timeout=self._timeout_s
            )
            response.raise_for_status()

            return
