from src.core.decorators import catch_and_log_exception
from src.core.exceptions import TaskNotFound
from src.domain.commands import Command
from src.service_layer.handlers.types import CommandHandlers
from src.service_layer.queue.task_queue import TaskQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW


class CommandQueue(TaskQueue[Command]):
    def __init__(self, handlers: CommandHandlers, uow: PublishingUoW):
        # TODO: Make max_running_items part of config?
        super().__init__(uow, handlers, max_running_items=10)

    @catch_and_log_exception()
    def _handle_item_failure(
        self, item: Command, uow: PublishingUoW, e: Exception
    ) -> None:
        with uow:
            task = uow.tasks.get(item.task_id)

            if not task:
                raise TaskNotFound(item.task_id)

            task.mark_failed(e)

            uow.tasks.save(task)

            uow.commit()

    def _get_priority(self, _: Command) -> int:
        # TODO: add priority logic
        return 1

    def _put_emitted_items(self):
        for command in self._uow.collect_new_commands():
            self.put(command)
