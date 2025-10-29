from typing import TypeVar

from src.adapters.config_repository import AbstractConfigRepository
from src.adapters.repository import AbstractRepository

RepoType = TypeVar(
    "RepoType", bound=AbstractRepository, default=AbstractRepository, covariant=True
)
ConfigRepoType = TypeVar(
    "ConfigRepoType",
    bound=AbstractConfigRepository,
    default=AbstractConfigRepository,
    covariant=True,
)
