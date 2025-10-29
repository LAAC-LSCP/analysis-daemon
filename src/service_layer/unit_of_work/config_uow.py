from abc import abstractmethod
from typing import Generic

from sqlalchemy.orm import Session

from src.service_layer.types import ConfigRepoType
from src.service_layer.unit_of_work import SessionFactory


class AbstractConfigUoW(Generic[ConfigRepoType]):
    """
    Similar to the regular uow, but for the configs table
    """

    configs: ConfigRepoType

    session_factory: SessionFactory
    session: Session

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.rollback()

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
