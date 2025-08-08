from pathlib import Path

import pytest

from src.service_layer.handlers import TaskCollisionError, add_task
from tests.integration.service_layer.fakes import FakeUoW
from tests.unit.service_layer.fakes import FakeRepository, TaskArgs


def test_adding_returns_task_id():
    uow = FakeUoW()

    result = add_task(
        owner_id=1,
        filesystem=Path("/path1"),
        uow=uow,
    )

    assert result == 1


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
        add_task(
            owner_id=3,
            filesystem=Path("/filesystem_path"),
            outputs=[Path("/output_1")],
            uow=uow,
        )


def test_commit():
    uow = FakeUoW()

    add_task(owner_id=1, filesystem=Path("."), uow=uow)

    assert uow.committed
