from typing import List, Optional, Union

from sqlalchemy.orm import Session

from src.adapters.repository import AbstractRepository
from src.domain.model import (
    FileSystem,
    ModelTaskDetails,
    ScriptTaskDetails,
    Task,
    TaskProperty,
)


class SQLAlchemyRepository(AbstractRepository):
    """
    A SQLAlchemy repository for tasks
    """

    _session: Session

    def __init__(self, session: Session):
        self._session = session

    def get(self, task_id: int) -> Optional[Task]:
        task: Task = self._session.query(Task).filter_by(id=task_id).one()

        if not task:
            return None

        model_details: ModelTaskDetails = (
            self._session.query(ModelTaskDetails)
            .filter_by(ModelTaskDetails._task_id == task_id)
            .first()
        )
        script_details: ScriptTaskDetails = (
            self._session.query(ScriptTaskDetails)
            .filter_by(ScriptTaskDetails._task_id == task_id)
            .first()
        )

        if script_details is not None:
            task.details = script_details
        elif model_details is not None:
            task.details = model_details
        else:
            raise ValueError("No details found for this task")

        return task

    def get_by_owner(self, owner_id: int) -> List[Task]:
        return self._session.query(Task).filter_by(Task.owner_id == owner_id)

    def get_by_filesystem(self, filesystem: FileSystem) -> List[Task]:
        if not filesystem._task_id:
            return []

        return (
            self._session.query(Task)
            .join(FileSystem)
            .filter(FileSystem._task_id == filesystem._task_id)
            .all()
        )

    def save(self, task: Task) -> Task:
        """
        Saves a task and automatically binds the `_id` parameter
        """

        self._session.add(task)
        self._session.flush()  # Force INSERT but don't commit to bind the id

        self._add_dependent_fields(task)

        return task

    def _add_dependent_fields(self, task: Task) -> None:
        assert task._id is not None, "Task ID should be set"

        id: int = task._id

        self._add_dependent_field(task.details, id)
        self._add_dependent_field(task.filesystem, id)
        self._add_dependent_field(task.outputs, id)
        self._add_dependent_field(task.inputs, id)

    def _add_dependent_field(
        self, details: Optional[Union[TaskProperty, List]], task_id: int
    ) -> None:
        if not details:
            return

        if isinstance(
            details, list
        ):  # recurse through to simple task details. Other plans too verbose
            for nested_details in details:
                self._add_dependent_field(nested_details, task_id)
        else:
            details._task_id = task_id

            self._session.add(details)
