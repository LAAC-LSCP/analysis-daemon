from typing import Any, Awaitable, Callable, List, Type

from src.domain.events import Event
from src.service_layer.publishing_uow import PublishingUoW
from src.service_layer.queue.queue import TaskQueue

EventCallback = Callable[[Any, PublishingUoW], Awaitable[None]]


class EventQueue(TaskQueue[Event]):
    _handlers: dict[Type[Event], List[EventCallback]]

    def __init__(
        self, handlers: dict[Type[Event], List[EventCallback]], uow: PublishingUoW
    ):
        super().__init__(uow)
        self._handlers = handlers

    async def _process_message(self) -> Event:
        event = await self._queue.get()
        try:
            await self._handle(event)
        finally:
            self._queue.task_done()
            return event

    async def _handle(self, event: Event) -> None:
        for handler in self._handlers[type(event)]:
            try:
                # TODO: log here
                await handler(event, self._uow)
                new_events = self._uow.collect_new_events()
                for e in new_events:
                    await self.put(e)
            except Exception:
                # TODO: log here
                continue
