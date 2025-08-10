import asyncio
from typing import Any, Awaitable, Callable, List, Optional, Type, Union

from src.domain import commands, events
from src.service_layer import handlers
from src.service_layer.uow import AbstractUoW

Message = Union[commands.Command, events.Event]


EventCallback = Callable[[Any, AbstractUoW], Awaitable[None]]
CommandCallback = Callable[[Any, AbstractUoW], Awaitable[Any]]


async def handle_task_started(_: events.TaskStarted, __: AbstractUoW) -> None:
    raise NotImplementedError


async def handle_task_completed(_: events.TaskCompleted, __: AbstractUoW) -> None:
    raise NotImplementedError


async def handle_task_failed(_: events.TaskFailed, __: AbstractUoW) -> None:
    raise NotImplementedError


async def handle_task_created(_: events.TaskQueued, __: AbstractUoW) -> None:
    raise NotImplementedError


# TODO: not the most elegant typing. Overloading by building up handler dict
# during bootstrapping phase seems significantly cleaner
_EVENT_HANDLERS: dict[Type[events.Event], List[EventCallback]] = {
    events.TaskStarted: [handle_task_started],
    events.TaskCompleted: [handle_task_completed],
    events.TaskFailed: [handle_task_failed],
    events.TaskQueued: [handle_task_created],
}

_COMMAND_HANDLERS: dict[Type[commands.Command], List[CommandCallback]] = {
    commands.MarkTaskAsComplete: [handlers.mark_task_complete],
    commands.CreateTask: [handlers.add_task],
}


class TaskQueue:
    _event_handlers: dict[Type[events.Event], List[EventCallback]]
    _command_handlers: dict[Type[commands.Command], List[CommandCallback]]
    _queue: asyncio.Queue
    _uow: AbstractUoW
    _results: List[Any]
    _shutdown: bool

    def __init__(
        self,
        uow: AbstractUoW,
        event_handlers: Optional[dict[Type[events.Event], List[EventCallback]]] = None,
        command_handlers: Optional[
            dict[Type[commands.Command], List[CommandCallback]]
        ] = None,
    ):
        self._queue = asyncio.Queue()
        self._event_handlers = event_handlers or _EVENT_HANDLERS
        self._command_handlers = command_handlers or _COMMAND_HANDLERS

        self._uow = uow
        self._results = []
        self._shutdown = False

    def shutdown(self) -> None:
        self._shutdown = True

    async def put(self, message: Message) -> None:
        await self._queue.put(message)

    async def process_messages(self) -> None:
        while not self._shutdown:
            await self._process_message()

    async def process_messages_until_empty(self) -> None:
        while not self._queue.empty():
            await self._process_message()

    async def _process_message(self) -> None:
        message = await self._queue.get()
        try:
            if isinstance(message, events.Event):
                await self._handle_event(message)
            elif isinstance(message, commands.Command):
                cmd_result = await self._handle_command(message)
                self._results.append(cmd_result)
        finally:
            self._queue.task_done()

    async def _handle_event(self, event: events.Event) -> None:
        for handler in self._event_handlers[type(event)]:
            try:
                # TODO: log here
                await handler(event, self._uow)
                new_events = self._uow.collect_new_events()
                for e in new_events:
                    await self.put(e)
            except Exception:
                # TODO: log here
                continue

    # TODO: typing here is a bit rough
    async def _handle_command(self, command: commands.Command) -> Any:
        for handler in self._command_handlers[type(command)]:
            try:
                # TODO: log here
                result = await handler(command, self._uow)
                new_events = self._uow.collect_new_events()
                for e in new_events:
                    await self.put(e)

                return result
            except Exception:
                # TODO: log here
                raise

        return None
