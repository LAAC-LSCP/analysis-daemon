import pytest

from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.queue.event_queue import EventQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
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

    queue.put(Command1())
    queue.put(Command2())

    await queue._tick()

    assert call_order == ["handler_1", "handler_2"]


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

    queue.put(Event1())
    queue.put(Event2())

    await queue._tick()

    assert call_order == ["handler_1", "handler_2"]
