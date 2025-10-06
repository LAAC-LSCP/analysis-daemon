from typing import Set

from src.domain.commands import Command
from src.domain.events import Event
from src.service_layer import Message
from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.queue.event_queue import EventQueue


class MessageBroker:
    """
    A broker that routes messages to its event and command queue respectively
    """

    _event_queue: EventQueue
    _command_queue: CommandQueue

    @property
    def queued_commands(self) -> Set[Command]:
        return self._command_queue.queued_messages

    def __init__(self, event_queue: EventQueue, command_queue: CommandQueue):
        self._event_queue = event_queue
        self._command_queue = command_queue

    def shutdown(self) -> None:
        self._event_queue.shutdown()
        self._command_queue.shutdown()

    async def put(self, message: Message) -> None:
        if isinstance(message, Event):
            await self._event_queue.put(message)
        elif isinstance(message, Command):
            await self._command_queue.put(message)
        else:
            raise ValueError(f"{message} not of type `Message` or `Command`")

    async def process_messages_until_empty(self) -> None:
        await self._event_queue.process_messages_until_empty()
        await self._command_queue.process_messages_until_empty()
