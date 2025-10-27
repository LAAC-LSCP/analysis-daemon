import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio.subprocess import Process
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import PriorityQueue
from typing import (
    Generic,
    List,
    Optional,
    Tuple,
)

from src.domain import commands
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
    _running_items: List[Tuple[MessageT, Process | None]]
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
        self._running_items = []
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
        num_items_to_pop = max(
            0,
            min(
                self._queue.qsize(), self._max_running_items - len(self._running_items)
            ),
        )

        for _ in range(num_items_to_pop):
            item: MessageT = self._queue.get().item
            await self._process_item(item)

        self._put_emitted_items()

    async def _process_item(self, item: MessageT) -> None:
        try:
            if self._is_external_job(item):
                proc: Process = await asyncio.create_subprocess_exec(
                    "echo",
                    "hello",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                self._running_items.append((item, proc))
                asyncio.create_task(self._monitor_job(item, proc))
            else:
                self._running_items.append((item, None))
                await self._run_python_job(item)
        except Exception:
            logger.exception(f"Exception processing item {item}")

    def _is_external_job(self, item: MessageT) -> bool:
        return isinstance(item, commands.CreateTask)

    async def _run_python_job(self, item: MessageT):
        for handler in self._handlers[type(item)]:  # type: ignore
            await handler(item, self._uow)

        self._atomic_remove_from_running_items(item)

    async def _monitor_job(self, item: MessageT, proc: Process):
        await proc.wait()

        self._atomic_remove_from_running_items(item)

        _, _ = await proc.communicate()

    def _atomic_remove_from_running_items(self, item: MessageT):
        self._running_items = [(m, p) for (m, p) in self._running_items if m != item]

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
