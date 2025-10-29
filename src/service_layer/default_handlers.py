import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Protocol, Type, TypeVar, Union

from src.config.config import ConfigModel
from src.core import response_types
from src.core.exceptions import TaskNotFound
from src.core.types import TaskStatus
from src.domain import commands, events
from src.domain.model import Task
from src.service_layer.http_client import HTTPClient
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW

type Message = Union[events.Event, commands.Command]
MessageCallback = Callable[[Any, PublishingUoW], Awaitable[Any]]


CommandT = TypeVar("CommandT", bound=commands.Command, contravariant=True)
EventT = TypeVar("EventT", bound=events.Event, contravariant=True)
MessageT = TypeVar("MessageT", bound=Message, contravariant=True)


class CommandHandler(Protocol[CommandT]):
    async def __call__(self, command: CommandT, uow: PublishingUoW) -> None: ...


class EventHandler(Protocol[EventT]):
    async def __call__(self, event: EventT, uow: PublishingUoW) -> None: ...


type CommandHandlers = Dict[Type[commands.Command], List[CommandHandler[Any]]]
type EventHandlers = Dict[Type[events.Event], List[EventHandler[Any]]]
type MessageHandlers = Union[CommandHandlers, EventHandlers]


logger = logging.getLogger(__name__)


async def handle_task_not_implemented(event: events.Event, uow: PublishingUoW) -> None:
    raise NotImplementedError


def get_update_echolalia_handler(
    task_status: TaskStatus, http_client: HTTPClient, config: ConfigModel
) -> EventHandler:
    async def handle_update_echolalia(event: events.Event, uow: PublishingUoW) -> None:
        response_task: response_types.Task
        with uow:
            task = uow.tasks.get(event.task_id)

            if task is None:
                # TODO: we can skip all this stuff when we complete the below todo
                raise ValueError(f"Task with ID {event.task_id} not found")

            response_task = task.to_response_type_task(config)

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


async def handle_create_task(
    command: commands.CreateTask,
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


def get_event_handlers(http_client: HTTPClient, config: ConfigModel) -> EventHandlers:
    return {
        events.TaskCreated: [handle_task_created],
        events.TaskStarted: [
            handle_task_started,
            get_update_echolalia_handler(TaskStatus.RUNNING, http_client, config),
        ],
        events.TaskFailed: [
            handle_task_failed,
            get_update_echolalia_handler(TaskStatus.FAILED, http_client, config),
        ],
        events.TaskCompleted: [
            handle_task_completed,
            get_update_echolalia_handler(TaskStatus.COMPLETED, http_client, config),
        ],
    }
