"""
The service layer consists of all application logic, above the level of mere
domain definitions (see domain layer)

This layer includes the command and event handlers, the command/event queues and
broker, and the unit of work abstraction
"""

from typing import TypeVar

from src.adapters.repository import AbstractRepository
from src.domain.commands import Command
from src.domain.events import Event

type Message = Event | Command
RepoType = TypeVar(
    "RepoType", bound=AbstractRepository, default=AbstractRepository, covariant=True
)
CallbackType = TypeVar("CallbackType", bound=Message)
