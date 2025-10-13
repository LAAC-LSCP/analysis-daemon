from typing import Any, Awaitable, Callable, List, Type

from src.domain.commands import Command
from src.service_layer.queue.queue import TaskQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

CommandCallback = Callable[[Any, PublishingUoW], Awaitable[Any]]


class CommandQueue(TaskQueue[Command]):
    _handlers: dict[Type[Command], List[CommandCallback]]

    def __init__(
        self, handlers: dict[Type[Command], List[CommandCallback]], uow: PublishingUoW
    ):
        super().__init__(uow)
        self._handlers = handlers

    async def _process_message(self) -> Command:
        command = await self._queue.get()
        try:
            result = await self._handle(command)
            self._results.append(result)
        finally:
            self._queue.task_done()
            return command

    async def _handle(self, command: Command) -> Any:
        for handler in self._handlers[type(command)]:
            try:
                # TODO: log here
                result = await handler(command, self._uow)
                new_commands = self._uow.collect_new_commands()
                for c in new_commands:
                    await self.put(c)

                return result
            except Exception:
                # TODO: log here
                raise
