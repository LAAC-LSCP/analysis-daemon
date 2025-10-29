from abc import ABC, abstractmethod
from typing import Optional, Tuple

from src.config.config import ConfigModel


class AbstractConfigRepository(ABC):
    """
    ABC for managing configuration versions in the database
    """

    @abstractmethod
    def get_latest_config(self) -> Optional[Tuple[ConfigModel, int]]:
        raise NotImplementedError

    @abstractmethod
    def save_config(self, data: ConfigModel) -> Tuple[ConfigModel, int]:
        raise NotImplementedError
