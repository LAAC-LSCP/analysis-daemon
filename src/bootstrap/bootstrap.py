import logging
from pathlib import Path

from src.config.config import load_config
from src.core.http_client import HTTPClient
from src.core.service import Service
from src.service_layer.publishing_uow import PublishingUoW
from src.service_layer.sqlalchemy_uow import SQLAlchemyUoW


def setup_logging():
    logging.basicConfig(level=logging.INFO)


def bootstrap(config_file: Path):
    config = load_config(config_file)

    sql_uow = PublishingUoW(
        SQLAlchemyUoW(
            session_factory=SQLAlchemyUoW.get_session_factory(config.database.url),
        )
    )

    http_client = HTTPClient(config.http.base_url)

    setup_logging()

    service = Service(
        uow=sql_uow,
        http_client=http_client,
        config=config,
    )

    return service
