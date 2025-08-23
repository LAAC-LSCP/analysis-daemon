import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Set, TypeVar

from src.service_layer import Message
from src.service_layer.publishing_uow import PublishingUoW

MessageType = TypeVar("MessageType", bound=Message)


class TaskQueue(ABC, Generic[MessageType]):
    queued_messages: Set[MessageType]  # Let us track inside the queue without pop
    _queue: asyncio.Queue[MessageType]
    _uow: PublishingUoW
    _results: List[Any]
    _shutdown: bool

    def __init__(
        self,
        uow: PublishingUoW,
    ):
        self._queue = asyncio.Queue()
        self.queued_messages = set()

        self._uow = uow
        self._results = []
        self._shutdown = False

    def shutdown(self) -> None:
        self._shutdown = True

    async def put(self, message: MessageType) -> None:
        await self._queue.put(message)
        self.queued_messages.add(message)

    async def process_messages_until_empty(self) -> None:
        while not self._queue.empty():
            message = await self._process_message()
            self.queued_messages.remove(message)

    @abstractmethod
    async def _process_message(self) -> MessageType:
        raise NotImplementedError

    @abstractmethod
    async def _handle(self, message: MessageType) -> Optional[Any]:
        raise NotImplementedError
