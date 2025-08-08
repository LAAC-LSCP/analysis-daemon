from typing import Any, Callable, List, Type

from src.domain import events
from src.service_layer import handlers
from src.service_layer.uow import AbstractUoW


def handle_start_task(_: events.TaskStarted, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle_complete_task(_: events.TaskCompleted, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle_failed_task(_: events.TaskFailed, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle(event: events.Event, uow: AbstractUoW):
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            handler(event, uow)
            queue.extend(uow.collect_new_events())


# TODO: not the most elegant typing. Overloading by building up handler dict
# during bootstrapping phase seems significantly cleaner
HANDLERS: dict[Type[events.Event], List[Callable[[Any, AbstractUoW], None]]] = {
    events.TaskStarted: [handle_start_task],
    events.TaskCompleted: [handle_complete_task],
    events.TaskFailed: [handle_failed_task],
    events.TaskCreated: [handlers.add_task],
    events.MarkTaskAsCompleted: [handlers.mark_task_complete],
}
