import platform
import socket
import tempfile
import time
import tomllib
import traceback
from multiprocessing import Process
from pathlib import Path

import pytest
import tomli_w

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


@pytest.fixture(scope="session")
def config_path():
    current_dir: Path = Path(__file__).parent

    config_file: Path = (
        current_dir / ".." / "fake_filesystem" / "configuration.toml"
    ).resolve()

    # The testing configuration.toml has relative paths. Need to replace with absolute
    with tempfile.NamedTemporaryFile(delete=True) as tf:
        config_as_toml: dict

        with open(config_file, "rb") as f:
            config_as_toml = tomllib.load(f)

        config_as_toml = _replace_relative_with_absolute_paths(
            config_as_toml,
            config_file,
        )

        tomli_w.dump(config_as_toml, tf)
        tf.flush()

        yield tf.name


def _replace_relative_with_absolute_paths(
    config_as_toml: dict, config_file: Path
) -> dict:
    config_as_toml["filesystems"] = [
        _fs_with_abs_path(fs, config_file) for fs in config_as_toml["filesystems"]
    ]

    return config_as_toml


def _fs_with_abs_path(fs: dict, config_file: Path) -> dict:
    fs["path"] = str((config_file.parent / fs["path"]).resolve())

    return fs


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
