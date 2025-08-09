from typing import Any, Callable, List, Type, Union

from src.domain import commands, events
from src.service_layer import handlers
from src.service_layer.uow import AbstractUoW

Message = Union[commands.Command, events.Event]


def handle_task_started(_: events.TaskStarted, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle_task_completed(_: events.TaskCompleted, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle_task_failed(_: events.TaskFailed, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle_task_created(_: events.TaskQueued, __: AbstractUoW) -> None:
    raise NotImplementedError


def handle(message: Message, uow: AbstractUoW):
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


def _handle_event(event: events.Event, queue: List[Message], uow: AbstractUoW) -> None:
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
    command: commands.Command, queue: List[Message], uow: AbstractUoW
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
_EVENT_HANDLERS: dict[Type[events.Event], List[Callable[[Any, AbstractUoW], None]]] = {
    events.TaskStarted: [handle_task_started],
    events.TaskCompleted: [handle_task_completed],
    events.TaskFailed: [handle_task_failed],
    events.TaskQueued: [handle_task_created],
}

_COMMAND_HANDLERS: dict[
    Type[commands.Command], List[Callable[[Any, AbstractUoW], Any]]
] = {
    commands.MarkTaskAsComplete: [handlers.mark_task_complete],
    commands.CreateTask: [handlers.add_task],
}
