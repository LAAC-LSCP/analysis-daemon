from dataclasses import dataclass

from src.core.types import UUID


class Event:
    pass


@dataclass
class TaskCreated(Event):
    task_id: UUID


@dataclass
class TaskStarted(Event):
    task_id: UUID


@dataclass
class TaskCompleted(Event):
    task_id: UUID


@dataclass
class TaskFailed(Event):
    task_id: UUID
    stack_trace: str
