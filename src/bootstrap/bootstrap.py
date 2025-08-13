import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.config import load_config
from src.core.service import Service
from src.service_layer.sqlalchemy_uow import SQLAlchemyUoW


def setup_logging():
    logging.basicConfig(level=logging.INFO)


def bootstrap(config_file: Path):
    config = load_config(config_file)

    SQL_uow = SQLAlchemyUoW(sessionmaker(bind=create_engine(config.database.url)))

    # TODO define a class for http server, instanciated at start up using\
    #  config, then the object is used to make requests
    # http_client = init_http_client(config.http.base_url)
    http_client = None

    setup_logging()

    service = Service(
        db_uow=SQL_uow,
        http_client=http_client,
        config=config,
    )

    return service
