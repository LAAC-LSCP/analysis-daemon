from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from src.adapters.repository import AbstractRepository
from src.domain.model import Task
from src.shared.types import UUID


class SQLAlchemyRepository(AbstractRepository):
    """
    A SQLAlchemy repository for tasks
    """

    _session: Session

    def __init__(self, session: Session):
        self._session = session

    def get(self, task_id: UUID) -> Optional[Task]:
        task: Optional[Task] = (
            self._session.query(Task).filter_by(_id=task_id).one_or_none()
        )

        return task

    def get_by_owner(self, owner_id: UUID) -> List[Task]:
        return self._session.query(Task).filter_by(owner_id=owner_id).all()

    def get_by_filesystem(self, filesystem_path: Path) -> List[Task]:
        return self._session.query(Task).filter_by(filesystem=filesystem_path).all()

    def save(self, task: Task) -> Task:
        """
        Saves a task and automatically binds the `_id` parameter
        """

        self._session.add(task)

        return task
