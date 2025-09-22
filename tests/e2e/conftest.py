import socket
import time
from multiprocessing import Process

import pytest

from tests.e2e.server import start_server

TEST_SERVER_DOMAIN: str = "127.0.0.1"
TEST_SERVER_PORT: int = 8001


def wait_for_server(host, port, timeout=5.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(
        f"Server at {host}:{port} did not start within {timeout} seconds"
    )


@pytest.fixture(scope="session", autouse=True)
def start_fake_server():
    proc = Process(target=start_server, args=())
    proc.start()
    wait_for_server(TEST_SERVER_DOMAIN, TEST_SERVER_PORT)
    yield
    proc.terminate()
