import asyncio
import logging

from src.core.exceptions import TaskNotFound
from src.domain import commands
from src.domain.model import Task
from src.service_layer.handlers.types import CommandHandlers
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

logger = logging.getLogger(__name__)


async def handle_create_task(
    command: commands.CreateTask,
    uow: PublishingUoW,
) -> None:
    task = Task(
        _id=command.task_id,
        owner_id=command.owner_id,
        dataset=command.dataset,
        status=command.status,
        operation=command.operation,
        config=command.config,  # TODO: temporary until join
    )
    with uow:
        uow.tasks.save(task)

        task.queue_task()

        uow.commit()


async def handle_run_task(
    command: commands.RunTask,
    uow: PublishingUoW,
) -> None:
    with uow:
        task = uow.tasks.get(command.task_id)

        if not task:
            raise TaskNotFound(command.task_id)

        if task.running:
            return

        task.start_run()
        uow.tasks.save(task)
        uow.commit()

    # TODO: this is kind of a blocking call for the task queue
    # But that is fine, since we will be using a job scheduler
    # which means this will be more or less instantaneous
    # although when we have the job scheduler set up, we'll
    # have to track when job completes in the task queue
    await _run_task(command)

    task.end_run()


async def handle_complete_task(
    command: commands.CompleteTask,
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


# TODO: move things to separate files
async def _run_task(command: commands.RunTask) -> None:
    # Execute the batch script through bash
    proc = await asyncio.create_subprocess_exec(
        "bash",
        str(command.script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_msg = (
            stderr.decode() if stderr else f"Script exited with code {proc.returncode}"
        )
        raise RuntimeError(f"Script execution failed: {error_msg}")

    logger.info(
        f"Script {command.script_path} run successfully for task {command.task_id}"
    )


def get_command_handlers() -> CommandHandlers:
    return {
        commands.CompleteTask: [handle_complete_task],
        commands.RunTask: [handle_run_task],
        commands.CreateTask: [handle_create_task],
    }
