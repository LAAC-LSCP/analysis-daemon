from typing import Callable, Optional, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.sqlalchemy_repository import SQLAlchemyRepository
from src.adapters.tracking_repository import TrackingRepository
from src.service_layer.uow import AbstractUoW

type SessionFactory = Callable[[], Session]


DEFAULT_SESSION_FACTORY: SessionFactory = sessionmaker(
    bind=create_engine("sqlite:///database.db")
)


class SQLAlchemyUoW(
    AbstractUoW[Union[SQLAlchemyRepository, TrackingRepository[SQLAlchemyRepository]]]
):
    session_factory: SessionFactory
    session: Session
    _tracking: bool

    def __init__(
        self,
        session_factory: SessionFactory = DEFAULT_SESSION_FACTORY,
        tracking: Optional[bool] = None,
    ):
        self.session_factory = session_factory
        self._tracking = tracking or True

    def __enter__(self) -> "SQLAlchemyUoW":
        self.session = self.session_factory()
        self.tasks = SQLAlchemyRepository(self.session)

        if self._tracking:
            self.tasks = TrackingRepository(self.tasks)

        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
