import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set

import src.core.response_types as response_types
from src.config.config import ConfigModel
from src.core.types import TaskStatus
from src.domain.commands import CreateTask
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
        self._uow = uow

        event_handlers = event_handlers or EVENT_HANDLERS
        command_handlers = command_handlers or COMMAND_HANDLERS

        event_queue = EventQueue(handlers=event_handlers, uow=uow)
        command_queue = CommandQueue(handlers=command_handlers, uow=uow)

        self._broker = MessageBroker(
            event_queue=event_queue, command_queue=command_queue
        )

        self._shutdown = False

    def shutdown(self) -> None:
        self._shutdown = True

    async def main_loop(self) -> None:
        await asyncio.gather(
            self._main_loop(),
            self._broker.event_queue.main_loop(),
            self._broker.command_queue.main_loop(),
        )

    async def _main_loop(self) -> None:
        while not self._shutdown:
            current_t = datetime.now()
            self._tick()

            sleep_t: float = (
                current_t + timedelta(seconds=self.S_PER_UPDATE) - datetime.now()
            ).total_seconds()

            await asyncio.sleep(sleep_t if sleep_t > 0 else 0)

        self._broker.shutdown()

    def _tick(self) -> None:
        with self._uow:
            new_tasks: Set[Task] = self._get_new_tasks()

            for task in new_tasks:
                self._broker.put(self._get_create_task_command(task))
                self._uow.tasks.save(task)

            self._uow.commit()

    def _get_new_tasks(self) -> Set[Task]:
        remote_tasks: response_types.Tasks = (
            self._http_client.get_all_tasks_with_status(TaskStatus.PENDING)
        )

        existing_tasks = self._uow.tasks.get_by_status(TaskStatus.PENDING)

        return set(
            task.to_model_type_task(config=self._config) for task in remote_tasks
        ) - set(existing_tasks)

    def _get_create_task_command(self, task: Task) -> CreateTask:
        # TODO: Probably don't need script_paths.
        # It's all clear from the config and model
        return CreateTask(
            task_id=task._id,
            owner_id=task.owner_id,
            filesystem=task.filesystem,
            script_path=task.script_path or Path(""),
            model=task.model,
        )
