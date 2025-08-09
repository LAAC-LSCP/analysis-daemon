from pathlib import Path

import pytest

import src.domain.commands as commands
import src.service_layer.message_bus as message_bus
from src.service_layer.handlers import TaskCollisionError
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fakes import FakeRepository, TaskArgs


def test_adding_returns_task_id():
    uow = FakeUoW()
    message_bus.handle(commands.CreateTask(owner_id=1, filesystem=Path("/path1")), uow)

    assert uow.tasks.get(task_id=1) is not None


def test_collisions_on_same_file_system():
    uow = FakeUoW()
    uow.tasks = FakeRepository.for_tasks(
        [
            TaskArgs(
                1,
                Path("/filesystem_path"),
                outputs=[Path("/output_1")],
            ),
            TaskArgs(
                2,
                Path("/filesystem_path"),
                outputs=[Path("/output_2")],
            ),
        ]
    )

    with pytest.raises(
        TaskCollisionError,
        match=(
            "Task collision in filesystem '/filesystem_path' detected on outputs: "
            "'/output_1'"
        ),
    ):
        message_bus.handle(
            commands.CreateTask(
                owner_id=3,
                filesystem=Path("/filesystem_path"),
                outputs=[Path("/output_1")],
            ),
            uow,
        )


def test_commit():
    uow = FakeUoW()

    message_bus.handle(commands.CreateTask(owner_id=1, filesystem=Path(".")), uow)

    assert uow.committed
