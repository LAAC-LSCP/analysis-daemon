from typing import Any, Callable, List, Type

from src.domain import commands, events
from src.domain.commands import Command
from src.service_layer import handlers
from src.service_layer.publishing_uow import PublishingUoW

type Message = events.Event | Command


def handle(message: Message, uow: PublishingUoW):
    results: List[Any] = []

    queue: List[Message] = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            _handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = _handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise ValueError(f"{message} was not an Event or Command")

    return results


def _handle_event(
    event: events.Event, queue: List[Message], uow: PublishingUoW
) -> None:
    for handler in _EVENT_HANDLERS[type(event)]:
        try:
            # TODO: log here
            handler(event, uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            # TODO: log here
            continue


# TODO: typing here is a bit rough
def _handle_command(
    command: commands.Command, queue: List[Message], uow: PublishingUoW
) -> Any:
    for handler in _COMMAND_HANDLERS[type(command)]:
        try:
            # TODO: log here
            result = handler(command, uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            # TODO: log here
            raise


# TODO: not the most elegant typing. Overloading by building up handler dict
# during bootstrapping phase seems significantly cleaner
_EVENT_HANDLERS: dict[
    Type[events.Event], List[Callable[[Any, PublishingUoW], None]]
] = {
    events.TaskStarted: [handlers.handle_not_implemented],
    events.TaskFailed: [handlers.handle_not_implemented],
    events.TaskCreated: [handlers.handle_not_implemented],
    events.TaskCompleted: [handlers.handle_not_implemented],
}

_COMMAND_HANDLERS: dict[
    Type[commands.Command], List[Callable[[Any, PublishingUoW], Any]]
] = {
    commands.CompleteTask: [handlers.handle_complete_task],
    commands.RunTask: [handlers.handle_run_task],
    commands.CreateTask: [handlers.handle_create_task],
}
