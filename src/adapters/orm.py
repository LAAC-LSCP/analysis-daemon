"""
This file contains all mapping information from the database to the ORM. We actually
use the repository pattern in our codebase, meaning that this mapping gets mapped
twice. This is important to keep in mind.
"""

import json
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    func,
)
from sqlalchemy.orm import registry, relationship
from sqlalchemy.types import String as StringType
from sqlalchemy.types import TypeDecorator

from src.core.types import ScriptArgs, ScriptFlags
from src.domain import model

metadata = MetaData()


class ArgsType(TypeDecorator):
    impl = StringType(length=256)

    def process_bind_param(self, value: ScriptArgs | None, _) -> str:
        if value is None:
            return json.dumps({})

        return json.dumps(value)

    def process_result_value(self, value: str | None, _) -> ScriptArgs:
        if value is None:
            return {}

        return json.loads(value)


class FlagsType(TypeDecorator):
    impl = StringType(length=256)

    def process_bind_param(self, value: ScriptFlags | None, _) -> str:
        if value is None:
            return json.dumps([])

        return json.dumps(value)

    def process_result_value(self, value: str | None, _) -> ScriptFlags:
        if value is None:
            return []

        return json.loads(value)


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
        return value.value  # type: ignore

    def process_result_value(self, value: Optional[str], _) -> model.TaskStatus:
        return model.TaskStatus(value)  # type: ignore


class OperationType(TypeDecorator):
    """
    Binds operation names to strings during forward/backwards object relational mapping
    """

    impl = StringType(length=256)

    def process_bind_param(self, value: Optional[model.Operation], _) -> str:
        return value.value  # type: ignore

    def process_result_value(self, value: Optional[str], _) -> model.Operation:
        return model.Operation(value)  # type: ignore


tasks = Table(
    "tasks",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner_id", String, nullable=False),
    Column("task_status", String, nullable=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("dataset", String, nullable=False),
    Column("operation", OperationType),
    Column("args", ArgsType, nullable=True),
    Column("flags", FlagsType, nullable=True),
    Column("config_version", Integer, ForeignKey("configs.version"), nullable=False),
)


configs = Table(
    "configs",
    metadata,
    Column("version", Integer, primary_key=True),
    Column("data", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
)


def start_mappers():
    mapper_registry = registry()

    mapper_registry.map_imperatively(
        model.Task,
        tasks,
        properties={
            "_id": tasks.c.id,
            "_config": relationship(model.Config, backref="tasks"),
            "config_version": tasks.c.config_version,
            "status": tasks.c.task_status,
        },
    )

    mapper_registry.map_imperatively(
        model.Config,
        configs,
    )
