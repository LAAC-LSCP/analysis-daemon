# TODO: add ways to mimicks faults in the communication, e.g., server down or packet
# lost

import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Set

import src.core.response_types as response_types
from src.core.types import UUID, Model, TaskStatus


class FakeServerHandler(BaseHTTPRequestHandler):
    """
    A fake test server. Runs in a separate process from the main test code and mimicks
    having a true distributed client-server system, albeit on the same machine
    """

    _tasks: Set[response_types.Task] = {
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
    }

    def do_GET(self):
        if self.path == "/api/analytics/tasks/":
            self._do_get_all_tasks()

            return

        if not self.path.startswith("/api/analytics/tasks/"):
            self._do_error()

            return

        path_end: str = self.path[len("/api/analytics/tasks/") :]

        if path_end in [status.value for status in TaskStatus]:
            self._do_get_tasks_by_status(path_end)

            return
        elif path_end.isdigit():
            self._do_get_task_by_id(path_end)
        else:
            self._do_error()

            return

    def do_POST(self):
        if not self.path == "/api/auth/login-service":
            self._do_error()

            return

        # Here we could get the payload but it's not really worth testing

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "access_token": "fake-token",
                    "expires_in": 100_000,
                    "token_type": "Bearer",
                }
            ).encode()
        )

    def do_PUT(self):
        if not self.path.startswith("/api/analytics/tasks/"):
            self._do_error()

            return

        id: UUID = UUID(self.path[len("/api/analytics/tasks/") :])

        if not id.isdigit():
            self._do_error()

            return

        content_length = int(self.headers.get("Content-Length", 0))
        body: bytes = self.rfile.read(content_length)
        payload: response_types.Task = json.loads(body.decode("utf-8"))

        task = next((t for t in self._tasks if t.id == id), None)

        if task is not None:
            self._tasks.remove(task)
        self._tasks.add(response_types.Task.from_dict({**{id: id}, **payload}))

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"result": "ok"}).encode())

    def do_DELETE(self):
        if not self.path.startswith("/api/analytics/tasks/"):
            self._do_error()
            return

        id_str = self.path[len("/api/analytics/tasks/") :]
        id = UUID(id_str)

        task = next((t for t in self._tasks if t.id == id), None)

        if task is not None:
            self._tasks.remove(task)
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
        else:
            self._do_error()

    def _do_get_all_tasks(self):
        self._do_get(
            [task.to_dict() for task in sorted(self._tasks, key=lambda task: task.id)]
        )

    def _do_get_tasks_by_status(self, status: str):
        tasks = [t for t in self._tasks if t.status == status]

        self._do_get(
            [task.to_dict() for task in sorted(tasks, key=lambda task: task.id)]
        )

    def _do_get_task_by_id(self, id: UUID):
        task = next((t for t in self._tasks if t.id == id), None)

        if task is None:
            self._do_get(None)
        else:
            self._do_get(task.to_dict())

    def _do_get(self, response: Any) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _do_error(self) -> None:
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()


def start_server_factory(host: str) -> Callable[[], None]:
    def start_server() -> None:
        """
        Creates a fake server. Mimicks Echolalia's server
        """
        server = HTTPServer((host, 8001), FakeServerHandler)
        server.serve_forever()

    return start_server
