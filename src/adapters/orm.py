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
from sqlalchemy.types import String as StringType
from sqlalchemy.types import TypeDecorator

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
