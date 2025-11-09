from pathlib import Path

from src.config.config import ConfigModel
from src.core.types import UUID, Operation
from src.domain.commands import CreateTask
from src.service_layer.queue.command_queue import CommandQueue
from src.service_layer.unit_of_work.publishing_uow import PublishingUoW
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fake_handlers import FakeHandlers


def test_command_queue_priority(config_model: ConfigModel):
    uow = PublishingUoW(FakeUoW())

    fake_handlers: FakeHandlers = FakeHandlers(uow)
    queue = CommandQueue(
        uow=uow,
        handlers=fake_handlers,  # type: ignore
    )

    command = CreateTask(
        task_id=UUID("1"),
        owner_id=UUID("Lawrence"),
        dataset="loann_2025",
        operation=Operation.VTC,
        config=config_model,
        input_folder=Path("."),
        input_files=[],
    )

    assert queue._get_priority(command) == 1
