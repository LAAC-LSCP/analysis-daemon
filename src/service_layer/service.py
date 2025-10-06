import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set

import src.core.response_types as response_types
from src.config.config import ConfigModel, FileSystemConfig
from src.core.decorators import catch_and_log_exception
from src.core.exceptions import (
    NoFileSystemWithDataset,
    NoFileSystemWithPath,
)
from src.core.types import UUID
from src.domain.commands import Command, CreateTask
from src.domain.model import Task
from src.service_layer.default_handlers import (
    COMMAND_HANDLERS,
    EVENT_HANDLERS,
    CommandHandlers,
    EventHandlers,
)
from src.service_layer.http_client import HTTPClient
from src.service_layer.queue.broker import MessageBroker
from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.queue.event_queue import EventQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW


class Service:
    """
    Main service object, runs the main loop of the program, stores configuration
    and interaction objects. Only one instance is meant to exist for the whole
    application and this instance acts as a composition root

    The program works by every so often querying Echolalia for new tasks
    Then doing some post-processing on the received tasks to avoid duplication
    And loading the tasks on the associated task queues

    TODO: consider how the application "ticks", that is, for now a tick loads on the
    queue and the queue handles all messages it has immediately and greedily

    But moving forward we might want to put the queues on their own threads and run
    them continuously, or (for testability) let queues themselves have an internal
    clock that ticks
    """

    S_PER_UPDATE: int = 10

    _broker: MessageBroker
    _http_client: HTTPClient
    _config: ConfigModel

    _shutdown: bool
    _uow: PublishingUoW

    def __init__(
        self,
        uow: PublishingUoW,
        http_client: HTTPClient,
        config: ConfigModel,
        event_handlers: Optional[EventHandlers] = None,
        command_handlers: Optional[CommandHandlers] = None,
    ):
        self._http_client = http_client
        self._config = config

        event_handlers = event_handlers or EVENT_HANDLERS
        command_handlers = command_handlers or COMMAND_HANDLERS

        event_queue = EventQueue(handlers=event_handlers, uow=uow)
        command_queue = CommandQueue(handlers=command_handlers, uow=uow)

        self._uow = uow

        self._broker = MessageBroker(
            event_queue=event_queue, command_queue=command_queue
        )

        self._shutdown = False

    def shutdown(self) -> None:
        self._shutdown = True

    async def main_loop(self) -> None:
        while not self._shutdown:
            current_t = datetime.now()
            await self._tick()

            sleep_t: float = (
                current_t + timedelta(seconds=self.S_PER_UPDATE) - datetime.now()
            ).total_seconds()

            await asyncio.sleep(sleep_t if sleep_t > 0 else 0)

        self._broker.shutdown()

    async def _tick(self) -> None:
        response = self._call_endpoint()

        for command in self._get_new_commands(response):
            await self._broker.put(command)

        await self._broker.process_messages_until_empty()

    def _call_endpoint(self) -> response_types.Tasks:
        return self._http_client.get_all_tasks()

    def _get_new_commands(self, response: response_types.Tasks) -> Set[Command]:
        # TODO: This logic is a mess, plus we put domain knowledge all the way up in
        # the service (importing Task). The question is, what do we do when a task is
        # off the queue? Do we cache it somewhere, so we know it is finished? Do we
        # have to access the db to see it is done? (most robust). Do we send a reply
        # to echolalia saying we have finished running the task, and now echolalia is
        # responsible for (very fragile and coupling!)? I went with the db solution,
        # although we get a dependency on Task which I have been trying to avoid
        # (jumping the component hierarchy that is)
        #
        # TODO: the best idea, I think, is to generate task IDs all the way up here
        # Use this to do equality checks
        owner_ids = {UUID(task.owner_id) for task in response}

        old_tasks = {
            self._get_cmd(self._convert_domain_task(task))
            for task in set(self._uow.tasks.get_by_owners(owner_ids=owner_ids))
        }

        old_tasks = old_tasks.union(self._broker._command_queue.queued_messages)

        tasks_in_response = {self._get_cmd(task) for task in set(response)}

        return tasks_in_response - old_tasks

    def _convert_domain_task(self, task: Task) -> response_types.Task:
        """
        Converts a task in the domain definition to one in the
        form of the network-defined task
        """
        fs: Optional[FileSystemConfig] = next(
            (fs for fs in self._config.filesystems if fs.path == task.filesystem), None
        )
        if fs is None:
            raise NoFileSystemWithPath(path=task.filesystem)

        if task.model is None:
            # TODO: Ditto. But model has a default "UNKNOWN" which is better
            # than script_path, which has no such default
            raise ValueError(f"Task {task} has no model")

        # TODO: code smell
        return response_types.Task(
            datetime=task.created_at,
            owner_id=task.owner_id,
            model_name=task.model,
            dataset_name=fs.dataset_name,
            status=task.status,
            id=task._id,
        )

    @catch_and_log_exception()
    def _get_cmd(self, task: response_types.Task) -> CreateTask:
        fs: Optional[FileSystemConfig] = next(
            (
                fs
                for fs in self._config.filesystems
                if fs.dataset_name == task.dataset_name
            ),
            None,
        )
        if fs is None:
            raise NoFileSystemWithDataset(dataset_name=task.dataset_name)

        return CreateTask(
            task_id=UUID(str(uuid.uuid4())),
            owner_id=task.owner_id,
            filesystem=fs.path,
            script_path=Path("fake-path"),  # TODO: get the script path from the config
            model=task.model_name,
        )
