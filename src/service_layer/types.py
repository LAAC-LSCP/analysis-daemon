from typing import TypeVar

from src.adapters.repository import AbstractRepository

RepoType = TypeVar(
    "RepoType", bound=AbstractRepository, default=AbstractRepository, covariant=True
)
