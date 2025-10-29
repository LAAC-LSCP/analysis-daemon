from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.sqlalchemy_config_repository import SQLAlchemyConfigRepository
from src.service_layer.unit_of_work import SessionFactory
from src.service_layer.unit_of_work.config_uow import AbstractConfigUoW


class SQLAlchemyConfigUoW(AbstractConfigUoW[SQLAlchemyConfigRepository]):
    """
    Similar to the SQLAlchemyUoW, but specifically for configs
    """

    @staticmethod
    def get_session_factory(db_url: str) -> SessionFactory:
        return sessionmaker(bind=create_engine(db_url))

    def __init__(
        self,
        session_factory: SessionFactory,
    ):
        self.session_factory = session_factory

    def __enter__(self) -> "SQLAlchemyConfigUoW":
        self.session = self.session_factory()
        self.configs = SQLAlchemyConfigRepository(self.session)

        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
