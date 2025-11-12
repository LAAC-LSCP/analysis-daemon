import asyncio
import logging
from pathlib import Path

from src.config.config import ConfigModel, ScriptConfig
from src.core.exceptions import NoScriptWithOperation, TaskNotFound
from src.core.filesystem import get_log_file, get_temp_dir, log_file_info
from src.domain import commands
from src.domain.model import Task
from src.service_layer.handlers.types import CommandHandler, CommandHandlers
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

logger = logging.getLogger(__name__)


def get_handle_create_task(config: ConfigModel) -> CommandHandler:
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
            input_folder=command.input_folder,
            input_files=command.input_files,
        )
        with uow:
            uow.tasks.save(task)

            task.queue_task(config)

            uow.commit()

    return handle_create_task


def get_handle_check_task(config: ConfigModel) -> CommandHandler:
    async def handle_check_task(
        command: commands.CheckTask, uow: PublishingUoW
    ) -> None:
        try:
            log_file: Path = get_log_file(config, command.task_id, command.dataset)
            succeeded_files, failed_files = log_file_info(log_file)

            is_done = set(command.input_files) == succeeded_files.union(failed_files)
        except Exception as e:
            logger.error(
                f"Problem checking output logs for task {command.task_id}: {e}"
            )

        with uow:
            task = uow.tasks.get(command.task_id)

            if not task:
                raise TaskNotFound(command.task_id)

            if not task.running:
                return

            if is_done:
                task.end_run()
            else:
                task.queue_status_check(config)

            uow.tasks.save(task)
            uow.commit()

        return

    return handle_check_task


def get_handle_run_task(config: ConfigModel) -> CommandHandler:
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

            task.start_run(config)
            uow.tasks.save(task)
            uow.commit()

        await _run_task(command, config)

    return handle_run_task


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


async def _run_task(command: commands.RunTask, config: ConfigModel) -> None:
    script: ScriptConfig | None = next(
        (script for script in config.scripts if script.model_name == command.operation),
        None,
    )

    if script is None:
        raise NoScriptWithOperation(command.operation)

    # Build the command arguments
    cmd_args = [
        "bash",
        str(config.script_wrapper),
        "--task-id",
        str(command.task_id),
        "--python-script",
        str(script.python_script_path),
        "--bash-script",
        str(script.bash_script_path),
        "--dataset",
        command.dataset,
        "--input-folder",
        str(command.input_folder),
        "--output-folder",
        str(command.output_folder),
        "--conda-src",
        str(config.conda_executable),
        "--env-name",
        script.env_name,
    ]

    for input_file in command.input_files:
        cmd_args.extend(["-i", str(input_file)])

    if config.jobs.use_slurm:
        job_name = (
            "echolalia" + "-" + str(command.operation) + "-" + str(command.task_id)
        )
        temp_folder = get_temp_dir(config)

        cmd_args = [
            "sbatch",
            f"--job-name={job_name}",
            "--partition=gpu",
            "--gres=gpu:1",
            f"--out={str(temp_folder / job_name) + ".out"}"
            f"--error={str(temp_folder / job_name) + ".err"}"
            "--output=%x-%j.log",
            "--error=",
        ] + cmd_args[
            1:
        ]  # remove "bash" part

    proc = await asyncio.create_subprocess_exec(
        *cmd_args,
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
        f"Operation {str(command.operation)} run successfully \
            for task {command.task_id}"
    )


def get_command_handlers(config: ConfigModel) -> CommandHandlers:
    return {
        commands.CompleteTask: [handle_complete_task],
        commands.RunTask: [get_handle_run_task(config)],
        commands.CheckTask: [get_handle_check_task(config)],
        commands.CreateTask: [get_handle_create_task(config)],
    }
