from typing import Any, Awaitable, Callable, List, Type

from src.domain import commands, events
from src.service_layer import handlers
from src.service_layer.publishing_uow import PublishingUoW

type EventHandlers = dict[
    Type[events.Event], List[Callable[[Any, PublishingUoW], Awaitable[None]]]
]

type CommandHandlers = dict[
    Type[commands.Command], List[Callable[[Any, PublishingUoW], Awaitable[Any]]]
]


# TODO: not the most elegant typing. Overloading by building up handler dict
# during bootstrapping phase seems significantly cleaner
_EVENT_HANDLERS: EventHandlers = {
    events.TaskStarted: [handlers.handle_not_implemented],
    events.TaskFailed: [handlers.handle_not_implemented],
    events.TaskCreated: [handlers.handle_not_implemented],
    events.TaskCompleted: [handlers.handle_not_implemented],
}

_COMMAND_HANDLERS: CommandHandlers = {
    commands.CompleteTask: [handlers.handle_complete_task],
    commands.RunTask: [handlers.handle_run_task],
    commands.CreateTask: [handlers.handle_create_task],
}
