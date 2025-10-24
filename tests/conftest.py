import shutil
import tempfile
import tomllib
from pathlib import Path
from typing import Generator

import pytest
import tomli_w
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, clear_mappers, sessionmaker

from src.adapters.orm import metadata, start_mappers
from src.config.config import ConfigModel, load_config


@pytest.fixture
def test_system_dir(tmp_path_factory) -> Path:
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
def config_path() -> Generator[Path]:
    current_dir: Path = Path(__file__).parent

    config_file: Path = current_dir / "fake_filesystem" / "configuration.toml"

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

        yield Path(tf.name)


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


@pytest.fixture(scope="session")
def config_model(config_path: Path) -> Generator[ConfigModel]:
    yield load_config(config_path)
