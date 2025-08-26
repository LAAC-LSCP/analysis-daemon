import pytest

from src.service_layer.publishing_uow import PublishingUoW
from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.queue.event_queue import EventQueue
from tests.integration.service_layer.fakes import (
    Command1,
    Command2,
    Event1,
    Event2,
    FakeUoW,
)


@pytest.mark.asyncio
async def test_command_queue_handling():
    call_order = []

    def get_mock_handler(num):
        async def mock_handler(*_):
            call_order.append(f"handler_{num}")
            return f"result_{num}"

        return mock_handler

    uow = PublishingUoW(FakeUoW())
    queue = CommandQueue(
        handlers={
            Command1: [get_mock_handler(1)],
            Command2: [get_mock_handler(2)],
        },
        uow=uow,
    )

    await queue.put(Command1())
    await queue.put(Command2())

    await queue.process_messages_until_empty()

    assert call_order == ["handler_1", "handler_2"]
    assert queue._results == ["result_1", "result_2"]


@pytest.mark.asyncio
async def test_event_queue_handling():
    call_order = []

    def get_mock_handler(num):
        async def mock_handler(*_):
            call_order.append(f"handler_{num}")
            return f"result_{num}"

        return mock_handler

    uow = PublishingUoW(FakeUoW())
    queue = EventQueue(
        handlers={
            Event1: [get_mock_handler(1)],
            Event2: [get_mock_handler(2)],
        },
        uow=uow,
    )

    await queue.put(Event1())
    await queue.put(Event2())

    await queue.process_messages_until_empty()

    assert call_order == ["handler_1", "handler_2"]
