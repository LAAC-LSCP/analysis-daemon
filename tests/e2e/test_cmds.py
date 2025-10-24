import subprocess
import tempfile
from pathlib import Path, PosixPath
from typing import Generator

import pytest


def test_package_installation():
    result = subprocess.run(
        ["pip", "show", "analysis-daemon", "--no-cache-dir"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "analysis-daemon" in result.stdout


def test_run_migrations_creates_db(temp_workspace: PosixPath, config_path: Path):
    result = subprocess.run(
        ["echolalia", "--config", str(config_path), "run-migrations"],
        capture_output=True,
        cwd=temp_workspace,
    )

    assert result.returncode == 0
    assert (temp_workspace / "database.db").exists()


@pytest.fixture(scope="session", autouse=True)
def install_package():
    result = subprocess.run(
        ["pip", "install", "-e", "."], capture_output=True, text=True
    )
    assert result.returncode == 0, f"Package installation failed: {result.stderr}"


@pytest.fixture
def temp_workspace() -> Generator[PosixPath]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield PosixPath(tmpdir)
