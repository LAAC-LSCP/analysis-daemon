import platform
import socket
import time
import traceback
from multiprocessing import Process

import pytest

from tests.e2e.fake_server import start_server

TEST_SERVER_DOMAIN: str = "localhost"
TEST_SERVER_PORT: int = 8520


def wait_for_server(host, port, timeout=5.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except Exception as e:
            print(f"Server failed to start: {e}", flush=True)
            traceback.print_exc()
            time.sleep(0.1)
    raise RuntimeError(
        f"Server at {host}:{port} did not start within {timeout} seconds"
    )


@pytest.fixture(scope="session", autouse=True)
def start_fake_server():
    if platform.system() == "Darwin":
        # TODO: fix this. Dockerise tests?
        yield

        return
    proc = Process(target=start_server, args=(TEST_SERVER_DOMAIN, TEST_SERVER_PORT))
    proc.start()
    wait_for_server(TEST_SERVER_DOMAIN, TEST_SERVER_PORT)

    yield

    proc.terminate()
    proc.join()
