import copy
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.adapters.sqlalchemy_config_repository import SQLAlchemyConfigRepository
from src.config.config import ConfigModel


def test_repository_saves_config(session: Session, config_model: ConfigModel):
    repo = SQLAlchemyConfigRepository(session)

    repo.save_config(config_model)
    session.commit()

    rows = session.execute(text("SELECT version, data, created_at FROM configs"))
    listed_rows = list(rows)

    assert len(listed_rows) == 1
    assert (listed_rows[0][0], json.loads(listed_rows[0][1])) == (
        0,
        json.loads(config_model.model_dump_json()),
    )


def test_repository_save_and_retrieve_config(
    session: Session, config_model: ConfigModel
):
    repo = SQLAlchemyConfigRepository(session)

    repo.save_config(config_model)
    session.commit()

    latest_config = repo.get_latest_config()

    assert latest_config is not None
    assert latest_config[0] == config_model
    assert latest_config[1] == 0


def test_repository_retrieve_nothing(session: Session):
    repo = SQLAlchemyConfigRepository(session)

    latest_config = repo.get_latest_config()

    assert latest_config is None


def test_repository_repeated_saves(session: Session, config_model: ConfigModel):
    repo = SQLAlchemyConfigRepository(session)

    repo.save_config(config_model)
    repo.save_config(config_model)
    repo.save_config(config_model)
    session.commit()

    latest_config = repo.get_latest_config()

    assert latest_config is not None
    assert latest_config[0] == config_model
    assert latest_config[1] == 0

    rows = session.execute(text("SELECT version FROM configs"))
    assert list(rows) == [(0,)]


def test_repository_save_configs(session: Session, config_model: ConfigModel):
    second_config: ConfigModel = copy.deepcopy(config_model)

    # second config will differ from the config_model
    second_config.scripts.pop()

    repo = SQLAlchemyConfigRepository(session)

    repo.save_config(config_model)
    session.commit()

    latest_config = repo.get_latest_config()

    assert latest_config is not None
    assert latest_config[0] == config_model
    assert latest_config[1] == 0

    repo.save_config(second_config)
    session.commit()

    latest_config = repo.get_latest_config()

    assert latest_config is not None
    assert latest_config[0] == second_config
    assert latest_config[1] == 1

    repo.save_config(config_model)
    session.commit()

    latest_config = repo.get_latest_config()

    assert latest_config is not None
    assert latest_config[0] == config_model
    assert latest_config[1] == 2
