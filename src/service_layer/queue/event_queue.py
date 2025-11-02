from src.core.decorators import catch_and_log_exception
from src.domain.events import Event
from src.service_layer.handlers.types import EventHandlers
from src.service_layer.queue.task_queue import TaskQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW


class EventQueue(TaskQueue[Event]):
    def __init__(self, handlers: EventHandlers, uow: PublishingUoW):
        # High number of running items (want to flush queue
        # immediately at every tick)
        super().__init__(uow, handlers, max_running_items=100_000)

        self._handlers = handlers

    @catch_and_log_exception()
    def _handle_item_failure(self, _: Event, __: PublishingUoW, e: Exception) -> None:
        raise (e)

    def _put_emitted_items(self):
        for event in self._uow.collect_new_events():
            self.put(event)

    def _get_priority(self, _: Event) -> int:
        # All messages are the same priority
        return 1
