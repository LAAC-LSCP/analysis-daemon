from typing import Any, Callable, List, Type

from src.domain import events
from src.service_layer import handlers
from src.service_layer.publishing_uow import PublishingUoW


def handle(event: events.Event, uow: PublishingUoW):
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            handler(event, uow)
            queue.extend(uow.collect_new_events())


# TODO: not the most elegant typing. Overloading by building up handler dict
# during bootstrapping phase seems significantly cleaner
HANDLERS: dict[Type[events.Event], List[Callable[[Any, PublishingUoW], None]]] = {
    events.TaskStarted: [handlers.handle_start_task],
    events.TaskFailed: [handlers.handle_failed_task],
    events.TaskCreated: [handlers.handle_create_task],
    events.TaskCompleted: [handlers.handle_complete_task],
}
