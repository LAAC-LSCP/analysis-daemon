import subprocess
from pathlib import Path

import pytest


def test_package_installation():
    result = subprocess.run(
        ["pip", "show", "analysis-daemon", "--no-cache-dir"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "analysis-daemon" in result.stdout


def test_run_migration(test_system_dir: Path, config_path: Path):
    result = subprocess.run(
        ["echolalia", "--config", str(config_path), "run-migrations"],
        capture_output=True,
        cwd=test_system_dir,
    )

    assert result.returncode == 0
    assert (test_system_dir / "database.db").exists()
    assert (test_system_dir / "log" / "echolalia.log").exists()


@pytest.fixture(scope="session", autouse=True)
def install_package():
    result = subprocess.run(
        ["pip", "install", "-e", "."], capture_output=True, text=True
    )
    assert result.returncode == 0, f"Package installation failed: {result.stderr}"
