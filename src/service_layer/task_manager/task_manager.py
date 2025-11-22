import asyncio
from pathlib import Path
from typing import List, Optional

from src.core.exceptions import InValidTaskStatus
from src.core.response_types import PostPayload, Task
from src.core.types import UUID, Operation, TaskStatus
from src.service_layer.http_client import HTTPClient


class TaskManager:
    _http_client: HTTPClient

    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def get(
        self, id: Optional[UUID] = None, status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Returns tasks received from the Echolalia server"""
        if id is not None and status is not None:
            task = self._http_client.get_task_by_id(UUID(id))

            if not task or not task.status == status:
                return []

            return [task]

        if id is not None:
            task = self._http_client.get_task_by_id(UUID(id))

            if not task:
                return []

            return [task]

        if status is not None:
            if status not in TaskStatus:
                raise InValidTaskStatus(status)

            tasks = self._http_client.get_all_tasks_with_status(TaskStatus(status))

            return tasks

        tasks = self._http_client.get_all_tasks()

        return tasks

    def post(self, analytics_uuid_label: UUID, dataset_uuid: UUID) -> Task:
        """Put a task on the remote server"""
        payload: PostPayload = {
            "analytics_uid_label": analytics_uuid_label,
            "uid_dataset": dataset_uuid,
            "kc_sub": "",
            "estimated_duration": 0,
        }

        task = self._http_client.post_task(payload)

        return task

    def put(
        self,
        id: UUID,
        input_folder: Path,
        owner_id: Optional[UUID] = None,
        task_status: Optional[TaskStatus] = None,
        operation: Optional[Operation] = None,
        dataset_name: Optional[str] = None,
        inputs: List[Path] = [],
    ) -> Task:
        """Create a task on the remote server
        If any field is unspecified, it fills it with the from the already existing task
        """
        existing_task = self._http_client.get_task_by_id(UUID(id))

        if not existing_task:
            raise ValueError(
                f"Task with UUID {id} does not exist. Did you mean \
                    to 'post' instead of 'put'?"
            )

        task = Task(
            datetime=existing_task.datetime,
            owner_id=owner_id or existing_task.owner_id,
            model_name=operation or existing_task.model_name,
            dataset_name=dataset_name or existing_task.dataset_name,
            status=task_status or existing_task.status,
            input_folder=input_folder,
            inputs=inputs,
            id=id,
        )

        asyncio.run(self._put_async(task))

        return task

    async def _put_async(self, task: Task):
        await self._http_client.put_task(task)
