import pytest

from src.service_layer.task_queue import TaskQueue
from tests.integration.service_layer.fakes import Command1, Command2, FakeUoW


@pytest.mark.asyncio
async def test_messages_processed_in_order():
    call_order = []

    def get_mock_handler(num):
        async def mock_handler(*_):
            call_order.append(f"handler_{num}")
            return f"result_{num}"

        return mock_handler

    uow = FakeUoW()
    queue = TaskQueue(
        uow,
        command_handlers={
            Command1: [get_mock_handler(1)],
            Command2: [get_mock_handler(2)],
        },
    )

    await queue.put(Command1())
    await queue.put(Command2())

    await queue.process_messages_until_empty()

    assert call_order == ["handler_1", "handler_2"]
    assert queue._results == ["result_1", "result_2"]


@pytest.mark.asyncio
async def test_command_handler_is_called():
    uow = FakeUoW()

    async def mock_handler(*_):
        return "test_result"

    queue = TaskQueue(uow, command_handlers={Command1: [mock_handler]})

    await queue.put(Command1())
    await queue.process_messages_until_empty()

    assert queue._results == ["test_result"]
