import logging

from src.core import response_types
from src.core.types import TaskStatus
from src.domain import events
from src.service_layer.handlers.types import EventHandler, EventHandlers
from src.service_layer.http_client import HTTPClient
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

logger = logging.getLogger(__name__)


def get_update_echolalia_handler(
    task_status: TaskStatus, http_client: HTTPClient
) -> EventHandler:
    async def handle_update_echolalia(event: events.Event, uow: PublishingUoW) -> None:
        response_task: response_types.Task
        with uow:
            task = uow.tasks.get(event.task_id)

            if task is None:
                # TODO: we can skip all this stuff when we complete the below todo
                raise ValueError(f"Task with ID {event.task_id} not found")

            response_task = task.to_response_type_task()

        response_task.status = task_status

        # TODO: negotiate with echolalia an endpoint to update a task's
        # status, and do nothing else
        await http_client.put_task(response_task)

        return

    return handle_update_echolalia


async def handle_task_started(event: events.TaskStarted, uow: PublishingUoW) -> None:
    logger.info(f"Task with ID {event.task_id} started")


async def handle_task_failed(event: events.TaskFailed, uow: PublishingUoW) -> None:
    logger.error(f"Task with ID {event.task_id} failed: {event.stack_trace}")


async def handle_task_created(event: events.TaskCreated, uow: PublishingUoW) -> None:
    logger.info(f"Task with ID {event.task_id} created")


async def handle_task_completed(
    event: events.TaskCompleted, uow: PublishingUoW
) -> None:
    logger.info(f"Task with ID {event.task_id} completed")


def get_event_handlers(http_client: HTTPClient) -> EventHandlers:
    return {
        events.TaskCreated: [handle_task_created],
        events.TaskStarted: [
            handle_task_started,
            get_update_echolalia_handler(TaskStatus.RUNNING, http_client),
        ],
        events.TaskFailed: [
            handle_task_failed,
            get_update_echolalia_handler(TaskStatus.FAILED, http_client),
        ],
        events.TaskCompleted: [
            handle_task_completed,
            get_update_echolalia_handler(TaskStatus.COMPLETED, http_client),
        ],
    }
