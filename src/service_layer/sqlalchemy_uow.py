from typing import Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.sqlalchemy_repository import SQLAlchemyRepository
from src.adapters.tracking_repository import TrackingRepository
from src.service_layer.uow import AbstractUoW

type SessionFactory = Callable[[], Session]


DEFAULT_DATABASE_URL: str = "sqlite:///database.db"


class SQLAlchemyUoW(AbstractUoW[TrackingRepository[SQLAlchemyRepository]]):
    session_factory: SessionFactory
    session: Session

    @staticmethod
    def get_session_factory(db_url: str) -> SessionFactory:
        return sessionmaker(bind=create_engine(db_url))

    def __init__(
        self,
        session_factory: Optional[SessionFactory] = None,
    ):
        self.session_factory = session_factory or self.get_session_factory(
            DEFAULT_DATABASE_URL
        )

    def __enter__(self) -> "SQLAlchemyUoW":
        self.session = self.session_factory()
        self.tasks = TrackingRepository(SQLAlchemyRepository(self.session))

        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
