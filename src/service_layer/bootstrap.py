import logging
import os
from pathlib import Path

from src.adapters.orm import start_mappers
from src.config.config import ConfigModel, load_config
from src.core.filesystem import (
    get_output_dir,
    get_temp_dir,
)
from src.service_layer.http_client import HTTPClient
from src.service_layer.service import Service
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from src.service_layer.unit_of_work.sqlalchemy_uow import SQLAlchemyUoW


def setup_logging(config: ConfigModel) -> logging.Logger:
    log_directory = config.log_directory

    log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    console_handler.setFormatter(console_format)

    if not log_directory.exists():
        log_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created log directory at: {str(log_directory)}")

    file_handler = logging.FileHandler(
        filename=os.path.join(log_directory, "echolalia.log"),
        mode="a",
        encoding="utf-8",
    )
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | "
        "%(process)d | %(threadName)s | %(message)s"
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


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
    start_mappers()

    sql_uow = PublishingUoW(
        SQLAlchemyUoW(
            session_factory=SQLAlchemyUoW.get_session_factory(config.database.url),
        )
    )

    http_client = get_http_client(config)

    config.echolalia_folder.mkdir(parents=True, exist_ok=True)
    get_temp_dir(config).mkdir(parents=True, exist_ok=True)
    get_output_dir(config).mkdir(parents=True, exist_ok=True)

    logger = setup_logging(config)

    service = Service(
        uow=sql_uow,
        http_client=http_client,
        config=config,
    )

    logger.info("Bootstrap phase complete")

    return service


def get_http_client(config_model: ConfigModel) -> HTTPClient:
    return HTTPClient(
        remote_api_url=str(config_model.http.base_url),
        client_id=config_model.http.client_id,
        client_secret=config_model.http.client_secret,
    )
