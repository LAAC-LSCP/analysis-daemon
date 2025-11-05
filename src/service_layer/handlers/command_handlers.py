import asyncio
import logging

from src.config.config import ConfigModel
from src.core.exceptions import TaskNotFound
from src.domain import commands
from src.domain.model import Task
from src.service_layer.handlers.types import CommandHandler, CommandHandlers
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

logger = logging.getLogger(__name__)


def get_handle_create_task(
    latest_config: ConfigModel, latest_version: int
) -> CommandHandler[commands.CreateTask]:
    async def handle_create_task(
        command: commands.CreateTask,
        uow: PublishingUoW,
    ) -> None:
        """
        Getting both latest version and latest config allows us to
        add config info, as it is not automatically done by the ORM

        Perhaps there's a better way of doing this.
        """
        operation = command.operation
        task = Task(
            _id=command.task_id,
            owner_id=command.owner_id,
            dataset=command.dataset,
            status=command.status,
            operation=operation.operation,
            args=operation.args,
            flags=operation.flags,
            config_version=latest_version,
            _config=latest_config,
        )
        with uow:
            uow.tasks.save(task)

            task.queue_task()

            uow.commit()

        return

    return handle_create_task


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


async def _run_task(command: commands.RunTask) -> None:
    operation = command.operation
    cmd_parts = ["bash", str(operation.script_path)]

    cmd_parts.extend(["--" + flag for flag in operation.flags])

    for key, value in operation.args.items():
        if value is not None:
            cmd_parts.append(f"--{key}={str(value)}")
        else:
            cmd_parts.append(f"--{key}")

    proc = await asyncio.create_subprocess_exec(
        *cmd_parts,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if stdout:
        logger.info(
            f"Script output for task {command.task_id}: {stdout.decode().strip()}"
        )

    if proc.returncode != 0:
        error_msg = (
            stderr.decode() if stderr else f"Script exited with code {proc.returncode}"
        )
        raise RuntimeError(f"Script execution failed: {error_msg}")

    logger.info(
        f"Script {operation.script_path} run successfully for task {command.task_id}"
    )


def get_command_handlers(
    latest_config: ConfigModel, latest_config_version: int
) -> CommandHandlers:
    return {
        commands.CompleteTask: [handle_complete_task],
        commands.RunTask: [handle_run_task],
        commands.CreateTask: [
            get_handle_create_task(latest_config, latest_config_version)
        ],
    }
