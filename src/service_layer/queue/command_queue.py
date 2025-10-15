from typing import Any

from src.domain.commands import Command
from src.service_layer.queue.task_queue import TaskQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW


class CommandQueue(TaskQueue[Command]):
    def __init__(self, handlers: Any, uow: PublishingUoW):
        # TODO: Make max_running_items part of config?
        super().__init__(uow, handlers, max_running_items=10)

    def _get_priority(self, _: Command) -> int:
        # TODO: add priority logic
        return 1
