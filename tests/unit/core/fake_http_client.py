from typing import List

from src.core.http_client import HTTPClient
from src.core.response_types import Tasks


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
