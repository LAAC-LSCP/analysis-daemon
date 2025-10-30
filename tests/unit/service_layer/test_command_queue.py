from pathlib import Path

from src.core.types import UUID, Model
from src.domain.commands import CreateTask
from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_handlers import FakeHandlers


def test_command_queue_priority():
    uow = PublishingUoW(FakeUoW())

    fake_handlers: FakeHandlers = FakeHandlers(uow)
    queue = CommandQueue(uow=uow, handlers=fake_handlers)

    command = CreateTask(
        task_id=UUID("1"),
        owner_id=UUID("Lawrence"),
        filesystem=Path("."),
        script_path=Path("."),
        model=Model.VTC,
    )

    assert queue._get_priority(command) == 1
