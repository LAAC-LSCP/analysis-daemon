from typing import List

from src.core.response_types import Task, Tasks
from src.core.types import TaskStatus
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

    def get_all_tasks_with_status(self, status: TaskStatus) -> Tasks:
        idx: int = self._counter % len(self._results)

        self._counter += 1

        return [result for result in self._results[idx] if result.status == status]

    async def put_task(self, task: Task) -> None:
        self._results.append([task])
