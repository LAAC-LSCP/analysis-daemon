from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.sqlalchemy_repository import SQLAlchemyRepository
from src.service_layer.uow import AbstractUoW

type SessionFactory = Callable[[], Session]


DEFAULT_SESSION_FACTORY: SessionFactory = sessionmaker(
    bind=create_engine("sqlite:///database.db")
)


class SQLAlchemyUoW(AbstractUoW):
    session_factory: SessionFactory
    session: Session

    def __init__(self, session_factory: SessionFactory = DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self) -> "SQLAlchemyUoW":
        self.session = self.session_factory()
        self.tasks = SQLAlchemyRepository(self.session)

        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
