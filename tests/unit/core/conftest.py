from pathlib import Path
from typing import List

import pytest
from pydantic import HttpUrl

from src.config.config import (
    ConfigModel,
    DatabaseConfig,
    FileSystemConfig,
    HTTPConfig,
    JobsConfig,
    ScriptConfig,
)

# TODO: Potentially replace some of these with factories later so we
# get a bit more flexibility in what we're testing


@pytest.fixture
def database_config() -> DatabaseConfig:
    # TODO: need better way of handling database URLs
    # Plus they are duplicated all over the codebase!
    return DatabaseConfig(url="sqlite:///:memory:")


@pytest.fixture
def jobs_config() -> JobsConfig:
    return JobsConfig(handler="sbatch", partition="test")


@pytest.fixture
def http_config() -> HTTPConfig:
    return HTTPConfig(base_url=HttpUrl("https://echolalia.example.com/api"))


@pytest.fixture
def filesystems_config(test_system_dir: Path) -> List[FileSystemConfig]:
    return [
        FileSystemConfig(
            dataset_name="loann-2025",
            path=test_system_dir / Path("datasets/loann_2025"),
            scripts=[
                ScriptConfig(script_name="run-model", script_path=Path("run_model.sh")),
                ScriptConfig(
                    script_name="calculate-aclew",
                    script_path=Path("calculate_aclew_metrics.sh"),
                ),
            ],
        )
    ]


@pytest.fixture
def config_model(
    database_config: DatabaseConfig,
    jobs_config: JobsConfig,
    http_config: HTTPConfig,
    filesystems_config: List[FileSystemConfig],
) -> ConfigModel:
    return ConfigModel(
        database=database_config,
        jobs=jobs_config,
        http=http_config,
        filesystems=filesystems_config,
    )
