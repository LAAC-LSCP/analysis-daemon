from enum import IntEnum
from typing import Any, List, Optional, Tuple, Type

import src.domain.commands as commands
import src.domain.events as events
from src.service_layer.default_handlers import (
    CommandHandler,
    CommandHandlers,
    EventHandler,
    EventHandlers,
    Message,
    get_command_handlers,
)
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

Calls = List[Tuple[Type[Message], Optional[Any]]]


class ExceptionResults(IntEnum):
    TASK_FAILURE = 0


class FakeHandlers:
    """
    A class encapsulating fake handlers

    When handlers are called it populates the `_calls` field
    Notably, the return values of the command handlers cycles over
    the `_command_results`
    """

    _command_handlers: CommandHandlers
    _event_handlers: EventHandlers

    _command_results: dict[Type[commands.Command], List[Any]]
    _results_counter: dict[Type[Message], int]

    _calls: Calls

    _uow: PublishingUoW

    @property
    def event_handlers(self) -> EventHandlers:
        return self._event_handlers

    @property
    def command_handlers(self) -> CommandHandlers:
        return self._command_handlers

    @property
    def calls(self) -> Calls:
        return self._calls

    def __init__(
        self,
        uow: PublishingUoW,
        command_results: Optional[dict[Type[commands.Command], List[Any]]] = None,
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
        command_results = command_results or {}

        self._command_results = {
            **{
                commands.StartTask: [None],
                commands.RunTask: [None],
                commands.CreateTask: [None],
                commands.CompleteTask: [None],
            },
            **command_results,
        }

        self._results_counter = {cmd_cls: 0 for cmd_cls in self._command_results}
        self._calls = []

        self._set_handlers()

    def _set_handlers(self) -> None:
        self._event_handlers = {
            events.TaskStarted: [self._get_event_callback(events.TaskStarted)],
            events.TaskCompleted: [self._get_event_callback(events.TaskCompleted)],
            events.TaskFailed: [self._get_event_callback(events.TaskFailed)],
            events.TaskCreated: [self._get_event_callback(events.TaskCreated)],
        }

        self._command_handlers = {
            cmd_cls: [self._get_command_callback(cmd_cls)]
            for cmd_cls in self._command_results
        }

    def set_command_handler(
        self, cls: Type[commands.Command], callbacks: List[CommandHandler]
    ) -> None:
        command_handlers = {**get_command_handlers(), **{cls: callbacks}}

        self._command_handlers = {
            cmd_cls: [
                self._get_command_callback(cmd_cls, command_handlers=command_handlers)
            ]
            for cmd_cls in self._command_results
        }

    def _get_event_callback(self, event_cls: Type[events.Event]) -> EventHandler:
        async def _call_event(event: events.Event, uow: PublishingUoW) -> None:
            self._calls.append((event_cls, None))

        return _call_event

    async def _call_event(self, cls: Type[events.Event], _: PublishingUoW) -> None:
        self._calls.append((cls, None))

    def _get_command_callback(
        self,
        cmd_cls: Type[commands.Command],
        command_handlers: Optional[CommandHandlers] = None,
    ) -> CommandHandler:
        command_handlers = command_handlers or get_command_handlers()

        async def _call_command(command: commands.Command, uow: PublishingUoW) -> Any:
            # For normal behaviour
            try:
                for handler in command_handlers[type(command)]:
                    await handler(command, uow)
            except Exception as e:
                self._calls.append((cmd_cls, ExceptionResults.TASK_FAILURE))

                raise (e)

            # For spying
            idx: int = self._results_counter[cmd_cls]
            result: Any = self._command_results[cmd_cls][idx]

            self._calls.append((cmd_cls, result))

            self._results_counter[cmd_cls] += 1
            self._results_counter[cmd_cls] %= len(self._command_results[cmd_cls])

            return result

        return _call_command
