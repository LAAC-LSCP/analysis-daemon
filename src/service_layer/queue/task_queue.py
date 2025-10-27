import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import PriorityQueue
from typing import (
    Generic,
    Optional,
)

from src.service_layer.default_handlers import MessageHandlers, MessageT
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PrioritizedItem(Generic[MessageT]):
    priority: int
    item: MessageT = field(compare=False)


class TaskQueue(ABC, Generic[MessageT]):
    S_PER_UPDATE: int = 30

    _max_running_items: int

    _queue: PriorityQueue
    _uow: PublishingUoW
    _shutdown: bool
    _handlers: MessageHandlers

    def __init__(
        self,
        uow: PublishingUoW,
        handlers: MessageHandlers,
        max_running_items: Optional[int] = None,
    ):
        self._uow = uow
        self._handlers = handlers

        self._max_running_items = max_running_items or 10
        self._queue = PriorityQueue()
        self._shutdown = False

    async def main_loop(self) -> None:
        while not self._shutdown:
            current_t = datetime.now()

            await self._tick()

            sleep_t: float = (
                current_t + timedelta(seconds=self.S_PER_UPDATE) - datetime.now()
            ).total_seconds()

            await asyncio.sleep(sleep_t if sleep_t > 0 else 0)

        self._queue.shutdown()

    def shutdown(self) -> None:
        self._shutdown = True

    async def _tick(self) -> None:
        self._put_emitted_items()

        num_items_to_pop = max(
            0,
            min(self._queue.qsize(), self._max_running_items),
        )

        for _ in range(num_items_to_pop):
            item: MessageT = self._queue.get().item
            await self._process_item(item)

    async def _process_item(self, item: MessageT) -> None:
        try:
            for handler in self._handlers[type(item)]:  # type: ignore
                await handler(item, self._uow)
        except Exception:
            logger.exception(f"Exception processing item {item}")

    def put(self, message: MessageT) -> None:
        priority = self._get_priority(message)

        prioritized_item = PrioritizedItem[MessageT](priority=priority, item=message)

        self._queue.put(prioritized_item)

    @abstractmethod
    def _put_emitted_items(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def _get_priority(self, _: MessageT) -> int:
        raise NotImplementedError
