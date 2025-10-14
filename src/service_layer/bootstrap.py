import logging
from pathlib import Path

from src.adapters.orm import start_mappers
from src.config.config import load_config
from src.service_layer.http_client import HTTPClient
from src.service_layer.service import Service
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from src.service_layer.unit_of_work.sqlalchemy_uow import SQLAlchemyUoW


def setup_logging():
    logging.basicConfig(level=logging.INFO)


def bootstrap(config_file: Path) -> Service:
    """
    Bootstraps the application, setting up:
    - Runtime configuration (from config file)
    - DB connections and the unit of work
    - The HTTP client for remote querying
    - Logging
    - And the service object

    The returned service objects acts as a composition root
    for the entire application
    """
    config = load_config(config_file)

    sql_uow = PublishingUoW(
        SQLAlchemyUoW(
            session_factory=SQLAlchemyUoW.get_session_factory(config.database.url),
        )
    )
    start_mappers()

    http_client = HTTPClient(
        remote_api_url=str(config.http.base_url),
        client_id=config.http.client_id,
        client_secret=config.http.client_secret,
    )

    setup_logging()

    service = Service(
        uow=sql_uow,
        http_client=http_client,
        config=config,
    )

    return service
