from typing import Any, Callable, List, Type

from src.domain.events import Event, TaskCompleted, TaskFailed, TaskStarted


def handle_start_task(_: TaskStarted) -> None:
    raise NotImplementedError


def handle_complete_task(_: TaskCompleted) -> None:
    raise NotImplementedError


def handle_failed_task(_: TaskFailed) -> None:
    raise NotImplementedError


def handle(event: Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


# TODO: not the most elegant typing. Overloading by building up handler dict
# during bootstrapping phase seems significantly cleaner
HANDLERS: dict[Type[Event], List[Callable[[Any], None]]] = {
    TaskStarted: [handle_start_task],
    TaskCompleted: [handle_complete_task],
    TaskFailed: [handle_failed_task],
}
