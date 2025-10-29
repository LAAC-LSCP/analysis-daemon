import json
from datetime import datetime
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.config import ConfigModel
from src.service_layer.unit_of_work.sqlalchemy_config_uow import SQLAlchemyConfigUoW
from src.service_layer.unit_of_work.sqlalchemy_uow import SessionFactory


class CustomException(Exception):
    pass


def _add_config(
    session: Session,
    config: ConfigModel,
    created_at: Optional[datetime] = None,
):
    data: str = config.model_dump_json()
    created_at = created_at or datetime.now()
    version = 0

    session.execute(
        text(
            (
                "INSERT INTO configs (version, data, created_at)"
                " VALUES (:version, :data, :created_at)"
            )
        ),
        dict(
            version=version,
            data=data,
            created_at=created_at,
        ),
    )


def test_uow_can_get(session_factory: SessionFactory, config_model: ConfigModel):
    session = session_factory()
    _add_config(session, config=config_model)
    session.commit()

    uow = SQLAlchemyConfigUoW(session_factory)

    with uow:
        latest_config = uow.configs.get_latest_config()

        assert latest_config is not None

        assert latest_config[0] == config_model
        assert latest_config[1] == 0


def test_uow_can_save(session_factory: SessionFactory, config_model: ConfigModel):
    uow = SQLAlchemyConfigUoW(session_factory)

    with uow:
        uow.configs.save_config(config_model)

        uow.commit()

    new_session = session_factory()
    rows = new_session.execute(text("SELECT version, data FROM configs"))
    listed_rows = list(rows)

    assert (listed_rows[0][0], json.loads(listed_rows[0][1])) == (
        0,
        json.loads(config_model.model_dump_json()),
    )


def test_uow_rolls_back_uncommitted_changes(
    session_factory: SessionFactory, config_model: ConfigModel
):
    uow = SQLAlchemyConfigUoW(session_factory)

    with uow:
        uow.configs.save_config(config_model)

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM configs")))
    assert rows == []


def test_rolls_back_on_error(
    session_factory: SessionFactory, config_model: ConfigModel
):
    uow = SQLAlchemyConfigUoW(session_factory)
    with pytest.raises(CustomException):
        with uow:
            uow.configs.save_config(config_model)
            raise CustomException()

    new_session = session_factory()
    rows = list(new_session.execute(text("SELECT * FROM configs")))
    assert rows == []
