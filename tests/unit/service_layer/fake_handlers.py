from typing import Any, List, Optional, Type, TypedDict

import src.domain.commands as commands
import src.domain.events as events
from src.service_layer.handlers.types import (
    CommandHandler,
    CommandHandlers,
    EventHandler,
    EventHandlers,
    Message,
)
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW


class Call(TypedDict):
    type: Type[Message]
    handler_name: str
    call_num: int
    message: Message


class FakeHandlers:
    """
    A class encapsulating fake handlers

    When handlers are called it populates the `_calls` field
    Notably, the return values of the command handlers cycles over
    the `_command_results`
    """

    _command_handlers: CommandHandlers
    _event_handlers: EventHandlers

    _call_count = 0
    _calls: List[Call]
    _exceptions: List[Call]

    _uow: PublishingUoW

    @property
    def event_handlers(self) -> EventHandlers:
        return self._event_handlers

    @property
    def command_handlers(self) -> CommandHandlers:
        return self._command_handlers

    @property
    def calls(self) -> List[Call]:
        return self._calls

    @property
    def exceptions(self) -> List[Call]:
        return self._exceptions

    def __init__(
        self,
        uow: PublishingUoW,
        command_handlers: Optional[CommandHandlers] = None,
        event_handlers: Optional[EventHandlers] = None,
    ):
        """
        Initialize the FakeHandlers.

        Args:
            command_results: Optional mapping of Command types to lists of results.
                Each handler will cycle through the provided results for its command
                type.

        Example:
            fake_handlers = FakeHandlers({
                commands.CreateTask: [result1, result2],
                commands.RunTask: [run_result],
            })
        """
        self._uow = uow

        self._calls = []
        self._exceptions = []

        self._command_handlers = command_handlers or {
            cmd: [FakeHandlers.empty_command_handler]
            for cmd in [
                commands.CreateTask,
                commands.StartTask,
                commands.RunTask,
                commands.CompleteTask,
            ]
        }
        self._event_handlers = event_handlers or {
            event: [FakeHandlers.empty_event_handler]
            for event in [
                events.TaskCreated,
                events.TaskStarted,
                events.TaskCompleted,
                events.TaskFailed,
            ]
        }

        self._command_handlers = {
            cmd: [self._track_command_handler(cmd, handler) for handler in handlers]
            for cmd, handlers in self._command_handlers.items()
        }
        self._event_handlers = {
            event: [self._track_event_handler(event, handler) for handler in handlers]
            for event, handlers in self._event_handlers.items()
        }

    def set_handlers_for_command(
        self, cmd_cls: Type[commands.Command], handlers: List[CommandHandler]
    ) -> None:
        self._command_handlers = {
            **self._command_handlers,
            **{
                cmd_cls: [
                    self._track_command_handler(cmd_cls, handler)
                    for handler in handlers
                ]
            },
        }

    def _track_command_handler(
        self, cmd_cls: Type[commands.Command], command_handler: CommandHandler
    ) -> CommandHandler:
        async def _call_command(command: commands.Command, uow: PublishingUoW) -> None:
            call = Call(
                type=cmd_cls,
                handler_name=str(command_handler.__name__),  # type: ignore
                call_num=self._call_count,
                message=command,
            )
            try:
                await command_handler(command, uow)
                self._calls.append(call)
                self._call_count += 1
            except Exception as e:
                self._exceptions.append(call)
                self._call_count += 1

                raise e

        return _call_command

    def _track_event_handler(
        self, event_cls: Type[events.Event], event_handler: EventHandler
    ) -> EventHandler:
        async def _call_event(event: events.Event, uow: PublishingUoW) -> None:
            call = Call(
                type=event_cls,
                handler_name=str(event_handler.__name__),  # type: ignore
                call_num=self._call_count,
                message=event,
            )
            try:
                await event_handler(event, uow)
                self._calls.append(call)
                self._call_count += 1
            except Exception as e:
                self._exceptions.append(call)
                self._call_count += 1

                raise e

        return _call_event

    @classmethod
    async def empty_command_handler(
        cls, command: commands.Command, uow: PublishingUoW
    ) -> Any:
        return

    @classmethod
    async def empty_event_handler(cls, event: events.Event, uow: PublishingUoW) -> Any:
        return
