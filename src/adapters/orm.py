from pathlib import Path

from sqlalchemy import (
    Boolean,
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

import src.domain.model as model

metadata = MetaData()


class PathType(TypeDecorator):
    """
    Lets us bind Paths to strings and vice versa during forward/backward mapping
    """

    impl = StringType(length=256)

    def process_bind_param(self, value: Path, _):
        return str(value)

    def process_result_value(self, value: str, _):
        return Path(value)


tasks = Table(
    "tasks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("owner_id", Integer, nullable=False),
    Column("completed", Boolean, nullable=False, default=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
)

filesystems = Table(
    "filesystems",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Integer, unique=True),
    Column("root_abs_path", PathType, nullable=False),
)

script_tasks = Table(
    "script_tasks",
    metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("script_file_rel_path", PathType, nullable=False),
)

model_tasks = Table(
    "model_tasks",
    metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("model_name", String(256), nullable=False),
)

inputs = Table(
    "inputs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Integer, ForeignKey("tasks.id")),
    Column("rel_path", PathType, nullable=True),
)

outputs = Table(
    "outputs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Integer, ForeignKey("tasks.id")),
    Column("rel_path", PathType, nullable=True),
)


def start_mappers():
    mapper_registry = registry()

    mapper_registry.map_imperatively(
        model.Task,
        tasks,
        properties={
            "_id": tasks.c.id,
            "inputs": relationship(
                model.TaskInput,
                primaryjoin=(tasks.c.id == inputs.c.task_id),
                uselist=True,
            ),
            "outputs": relationship(
                model.TaskOutput,
                primaryjoin=(tasks.c.id == outputs.c.task_id),
                uselist=True,
            ),
        },
    )
    mapper_registry.map_imperatively(
        model.FileSystem,
        filesystems,
        properties={
            "_task_id": filesystems.c.task_id,
            "root_abs_path": filesystems.c.root_abs_path,
        },
    )
    mapper_registry.map_imperatively(
        model.ModelTaskDetails,
        model_tasks,
        properties={
            "_task_id": model_tasks.c.task_id,
            "model_name": model_tasks.c.model_name,
        },
    )
    mapper_registry.map_imperatively(
        model.ScriptTaskDetails,
        script_tasks,
        properties={
            "_task_id": script_tasks.c.task_id,
            "script_path": script_tasks.c.script_file_rel_path,
        },
    )
    mapper_registry.map_imperatively(
        model.TaskInput,
        inputs,
        properties={
            "_task_id": inputs.c.task_id,
            "rel_path": inputs.c.rel_path,
        },
    )
    mapper_registry.map_imperatively(
        model.TaskOutput,
        outputs,
        properties={
            "_task_id": outputs.c.task_id,
            "rel_path": outputs.c.rel_path,
        },
    )
