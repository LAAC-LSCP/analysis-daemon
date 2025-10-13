"""
This file contains all mapping information from the database to the ORM. We actually
use the repository pattern in our codebase, meaning that this mapping gets mapped
twice. This is important to keep in mind.
"""

from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    func,
)
from sqlalchemy.orm import registry
from sqlalchemy.types import String as StringType
from sqlalchemy.types import TypeDecorator

from src.domain import model

metadata = MetaData()


class PathType(TypeDecorator):
    """
    Binds paths to strings during forward/backwards object relational mapping
    """

    impl = StringType(length=256)

    def process_bind_param(self, value: Path | None, _) -> str:
        return str(value or "")

    def process_result_value(self, value: str | None, _) -> Path:
        return Path(value or "")


class TaskStatusType(TypeDecorator):
    """
    Binds task status names to strings during forward/backwards object relational
    mapping
    """

    impl = StringType(length=256)

    def process_bind_param(self, value: Optional[model.TaskStatus], _) -> str:
        if value is None:
            return model.TaskStatus.UNKNOWN.value

        return value.value

    def process_result_value(self, value: Optional[str], _) -> model.TaskStatus:
        if value is None:
            return model.TaskStatus.UNKNOWN

        return model.TaskStatus(value)


class ModelType(TypeDecorator):
    """
    Binds model names to strings during forward/backwards object relational mapping
    """

    impl = StringType(length=256)

    def process_bind_param(self, value: Optional[model.Model], _) -> str:
        if value is None:
            return model.Model.UNKNOWN.value

        return value.value

    def process_result_value(self, value: Optional[str], _) -> model.Model:
        if value is None:
            return model.Model.UNKNOWN

        return model.Model(value)


tasks = Table(
    "tasks",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner_id", String, nullable=False),
    Column("task_status", String, nullable=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("filesystem_path", PathType, nullable=False),
    Column("script_rel_path", PathType),
    Column("model", ModelType),
)


def start_mappers():
    mapper_registry = registry()

    mapper_registry.map_imperatively(
        model.Task,
        tasks,
        properties={
            "_id": tasks.c.id,
            "status": tasks.c.task_status,
            "filesystem": tasks.c.filesystem_path,
            "script_path": tasks.c.script_rel_path,
        },
    )
