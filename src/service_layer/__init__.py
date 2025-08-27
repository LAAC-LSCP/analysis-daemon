from typing import TypeVar

from src.adapters.repository import AbstractRepository
from src.domain.commands import Command
from src.domain.events import Event

type Message = Event | Command
RepoType = TypeVar(
    "RepoType", bound=AbstractRepository, default=AbstractRepository, covariant=True
)
CallbackType = TypeVar("CallbackType", bound=Message)
