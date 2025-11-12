import shutil
import tomllib
from pathlib import Path
from typing import Generator

import pytest
import tomli_w
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, clear_mappers, sessionmaker

from src.adapters.orm import metadata, start_mappers
from src.config.config import ConfigModel, load_config


@pytest.fixture(scope="session")
def test_system_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    A temporary copy of the fake filesystem directory
    """
    src = Path(__file__).parent / "fake_filesystem"
    dst = tmp_path_factory.mktemp("fake_filesystem")
    shutil.copytree(src, dst, dirs_exist_ok=True)

    return dst


@pytest.fixture
def in_memory_db() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)

    return engine


@pytest.fixture
def session_factory(in_memory_db) -> Generator[sessionmaker]:
    start_mappers()
    try:
        yield sessionmaker(bind=in_memory_db)
    finally:
        clear_mappers()


@pytest.fixture
def session(session_factory) -> Generator[Session]:
    return session_factory()


@pytest.fixture(scope="session")
def config_path(test_system_dir: Path) -> Generator[Path]:
    fake_filesystem_dir: Path = Path(__file__).parent / "fake_filesystem"
    config_file: Path = fake_filesystem_dir / "configuration.toml"
    temp_config_file: Path = test_system_dir / "configuration.toml"

    # The testing configuration.toml has relative paths. Need to replace with absolute
    with open(config_file, "rb") as f:
        config_as_toml = tomllib.load(f)

    temp_config_as_toml = _replace_relative_with_absolute_paths(
        config_as_toml,
        temp_config_file,
    )

    with open(temp_config_file, "wb") as tf:
        tomli_w.dump(temp_config_as_toml, tf)

    yield temp_config_file


def _replace_relative_with_absolute_paths(
    config_as_toml: dict, config_file: Path
) -> dict:
    config_as_toml["scripts"] = [
        _script_item_w_abs_path(script, config_file)
        for script in config_as_toml["scripts"]
    ]
    config_as_toml["log_directory"] = _str_as_abs_path(
        config_as_toml["log_directory"], config_file
    )
    config_as_toml["conda_executable"] = _str_as_abs_path(
        config_as_toml["conda_executable"], config_file
    )
    config_as_toml["script_wrapper"] = _str_as_abs_path(
        config_as_toml["script_wrapper"], config_file
    )
    config_as_toml["echolalia_folder"] = _str_as_abs_path(
        config_as_toml["echolalia_folder"], config_file
    )

    return config_as_toml


def _script_item_w_abs_path(item: dict, config_file: Path) -> dict:
    item["python_script_path"] = str(
        (config_file.parent / item["python_script_path"]).resolve()
    )
    item["bash_script_path"] = str(
        (config_file.parent / item["bash_script_path"]).resolve()
    )

    return item


def _str_as_abs_path(rel_path: str, config_file: Path) -> str:
    return str((config_file.parent / Path(rel_path)).resolve())


@pytest.fixture(scope="session")
def config_model(config_path: Path) -> Generator[ConfigModel]:
    yield load_config(config_path)
