import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.response_types import PostPayload, Task, Tasks
from src.core.types import UUID, Operation, TaskStatus
from src.service_layer.http_client import HTTPClient


class FakeHTTPClient(HTTPClient):
    """
    Fake HTTP Client
    Everytime the endpoint is called and cycles over the results
    supplied in the constructor
    """

    _results: List[Tasks]
    _counter: int

    def __init__(self, results: List[Tasks]):
        self._counter = 0
        self._results = results

    def get_all_tasks(self) -> Tasks:
        idx: int = self._counter % len(self._results)

        self._counter += 1

        return self._results[idx]

    def get_task_by_id(self, id: UUID) -> Optional[Task]:
        idx: int = self._counter % len(self._results)

        self._counter += 1

        return next((result for result in self._results[idx] if result.id == id), None)

    def get_all_tasks_with_status(self, status: TaskStatus) -> Tasks:
        idx: int = self._counter % len(self._results)

        self._counter += 1

        return [result for result in self._results[idx] if result.status == status]

    def post_task(self, _: PostPayload) -> Task:
        task = Task(
            datetime=datetime.now(),
            owner_id=UUID("123"),
            model_name=Operation.VTC,
            dataset_name="loann_2025",
            status=TaskStatus.PENDING,
            inputs=[],
            input_folder=Path(""),
            id=UUID(str(uuid.uuid4())),
        )

        self._results = [self._append_task(result, task) for result in self._results]

        return task

    async def put_task(self, task: Task) -> None:
        self._results = [
            [self._set_status(t, task.status) if t.id == task.id else t for t in r]
            for r in self._results
        ]

        return

    def _append_task(self, result: List[Task], task: Task) -> List[Task]:
        result += [task]

        return result

    def _set_status(self, task: Task, status: TaskStatus) -> Task:
        task.status = status

        return task
