from typing import Any, Awaitable, Callable, Dict, List, Protocol, Type, TypeVar, Union

from src.domain import commands, events
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

type Message = Union[events.Event, commands.Command]
MessageCallback = Callable[[Any, PublishingUoW], Awaitable[Any]]


CommandT = TypeVar("CommandT", bound=commands.Command, contravariant=True)
EventT = TypeVar("EventT", bound=events.Event, contravariant=True)
MessageT = TypeVar("MessageT", bound=Message, contravariant=True)


class CommandHandler(Protocol[CommandT]):
    async def __call__(self, command: CommandT, uow: PublishingUoW) -> None: ...


class EventHandler(Protocol[EventT]):
    async def __call__(self, event: EventT, uow: PublishingUoW) -> None: ...


type CommandHandlers = Dict[Type[commands.Command], List[CommandHandler[Any]]]
type EventHandlers = Dict[Type[events.Event], List[EventHandler[Any]]]
type MessageHandlers = Union[CommandHandlers, EventHandlers]
