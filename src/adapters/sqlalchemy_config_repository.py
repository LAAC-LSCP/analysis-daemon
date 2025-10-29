import json
from typing import Dict, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.adapters.config_repository import AbstractConfigRepository
from src.config.config import ConfigModel
from src.domain.model import Config


class SQLAlchemyConfigRepository(AbstractConfigRepository):
    """SQLAlchemy implementation of ConfigRepository"""

    def __init__(self, session: Session):
        self.session = session

    def get_latest_config(self) -> Optional[Tuple[ConfigModel, int]]:
        latest_config: Config | None = self._get_latest_config()

        if latest_config is None:
            return None

        return (
            ConfigModel.model_validate_json(json.dumps(latest_config.data)),
            latest_config.version,
        )

    def save_config(self, config: ConfigModel) -> Tuple[ConfigModel, int]:
        """
        Saves config if it is not the same as the latest configuration
        """
        data: Dict = json.loads(config.model_dump_json())

        latest_config: Config | None = self._get_latest_config()

        if latest_config is not None and latest_config.data == data:
            return config, latest_config.version

        next_version: int

        if latest_config is None:
            next_version = 0
        else:
            next_version = (latest_config.version + 1) if latest_config else 1

        new_config = Config(version=next_version, data=data)
        self.session.add(new_config)

        return (
            ConfigModel.model_validate_json(json.dumps(new_config.data)),
            new_config.version,
        )

    def _get_latest_config(self) -> Optional[Config]:
        return (
            self.session.query(Config)
            .order_by(desc(Config.version))  # type: ignore
            .first()
        )
