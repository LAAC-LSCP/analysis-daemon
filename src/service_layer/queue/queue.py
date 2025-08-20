import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from src.service_layer.message_bus import Message
from src.service_layer.publishing_uow import PublishingUoW

MessageType = TypeVar("MessageType", bound=Message)


class TaskQueue(ABC, Generic[MessageType]):
    _queue: asyncio.Queue[MessageType]
    _uow: PublishingUoW
    _results: List[Any]
    _shutdown: bool

    def __init__(
        self,
        uow: PublishingUoW,
    ):
        self._queue = asyncio.Queue()

        self._uow = uow
        self._results = []
        self._shutdown = False

    def shutdown(self) -> None:
        self._shutdown = True

    async def put(self, message: MessageType) -> None:
        await self._queue.put(message)

    async def process_messages(self) -> None:
        while not self._shutdown:
            await self._process_message()

    async def process_messages_until_empty(self) -> None:
        while not self._queue.empty():
            await self._process_message()

    @abstractmethod
    async def _process_message(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _handle(self, message: MessageType) -> Optional[Any]:
        raise NotImplementedError
