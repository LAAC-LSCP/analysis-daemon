from src.domain.events import Event
from src.service_layer.default_handlers import EventHandlers
from src.service_layer.queue.task_queue import TaskQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW


class EventQueue(TaskQueue[Event]):
    def __init__(self, handlers: EventHandlers, uow: PublishingUoW):
        # High number of running items (want to flush queue
        # immediately at every tick)
        super().__init__(uow, handlers, max_running_items=100_000)

        self._handlers = handlers

    def _get_priority(self, _: Event) -> int:
        # All messages are the same priority
        return 1
