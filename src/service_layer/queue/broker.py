from src.domain.commands import Command
from src.domain.events import Event
from src.service_layer.default_handlers import Message
from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.queue.event_queue import EventQueue


class MessageBroker:
    """
    A broker that routes messages to its event and command queue respectively
    """

    event_queue: EventQueue
    command_queue: CommandQueue

    def __init__(self, event_queue: EventQueue, command_queue: CommandQueue):
        self.event_queue = event_queue
        self.command_queue = command_queue

    def shutdown(self) -> None:
        self.event_queue.shutdown()
        self.command_queue.shutdown()

    def put(self, message: Message) -> None:
        if isinstance(message, Event):
            self.event_queue.put(message)
        elif isinstance(message, Command):
            self.command_queue.put(message)
        else:
            raise ValueError(f"{message} not of type `Message` or `Command`")
