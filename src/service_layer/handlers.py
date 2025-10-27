import logging

from src.core.exceptions import TaskNotFound
from src.domain.commands import CompleteTask, CreateTask, RunTask
from src.domain.events import Event, TaskCompleted, TaskCreated, TaskFailed, TaskStarted
from src.domain.model import Task
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

logger = logging.getLogger(__name__)


async def handle_task_not_implemented(event: Event, uow: PublishingUoW) -> None:
    raise NotImplementedError


async def handle_task_started(event: TaskStarted, uow: PublishingUoW) -> None:
    logger.info(f"Task with ID {event.task_id} started")


async def handle_task_failed(event: TaskFailed, uow: PublishingUoW) -> None:
    logger.error(f"Task with ID {event.task_id} failed: {event.stack_trace}")


async def handle_task_created(event: TaskCreated, uow: PublishingUoW) -> None:
    logger.info(f"Task with ID {event.task_id} created")


async def handle_task_completed(event: TaskCompleted, uow: PublishingUoW) -> None:
    logger.info(f"Task with ID {event.task_id} completed")


async def handle_create_task(
    command: CreateTask,
    uow: PublishingUoW,
) -> None:
    task = Task(
        _id=command.task_id,
        owner_id=command.owner_id,
        filesystem=command.filesystem,
        model=command.model,
        script_path=command.script_path,
    )
    with uow:
        uow.tasks.save(task)

        task.queue_task()

        uow.commit()


async def handle_run_task(
    command: RunTask,
    uow: PublishingUoW,
) -> None:
    with uow:
        task = uow.tasks.get(command.task_id)

        if not task:
            raise TaskNotFound(command.task_id)

        if task.running:
            return

        task.run()

        uow.tasks.save(task)

        uow.commit()


async def handle_complete_task(
    command: CompleteTask,
    uow: PublishingUoW,
) -> None:
    with uow:
        task = uow.tasks.get(command.task_id)

        if not task:
            raise TaskNotFound(command.task_id)

        if task.completed:
            return

        task.mark_completed()

        uow.tasks.save(task)

        uow.commit()
