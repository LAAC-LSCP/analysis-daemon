from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
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
    Binds paths to strings during forward/backwards object relational mapping
    """

    impl = StringType(length=256)

    def process_bind_param(self, value: Path | None, _) -> str:
        return str(value or "")

    def process_result_value(self, value: str | None, _) -> Path:
        return Path(value or "")


tasks = Table(
    "tasks",
    metadata,
    Column("id", String, primary_key=True),
    Column("owner_id", Integer, nullable=False),
    Column("task_status", String, nullable=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("filesystem_path", PathType, nullable=False),
    Column("script_rel_path", PathType),
    Column("model", String),
)
