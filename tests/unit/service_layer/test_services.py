from pathlib import Path

import pytest

from src.domain.model import FileSystem, Task, TaskOutput
from src.service_layer.services import TaskCollisionError, add_task
from tests.unit.service_layer.fakes import FakeRepository, FakeSession


def test_adding_returns_task_id():
    task_1 = Task(owner_id=1, filesystem=Path("/path1"))

    repo = FakeRepository()

    result = add_task(task_1, repo, FakeSession())

    assert result == 1


def test_collisions_on_same_file_system():
    task_1 = Task(
        owner_id=1,
        filesystem=FileSystem("/filesystem_path"),
        outputs=[TaskOutput("/output_1")],
    )
    task_2 = Task(
        owner_id=2,
        filesystem=FileSystem("/filesystem_path"),
        outputs=[TaskOutput("/output_2")],
    )
    task_3 = Task(
        owner_id=3,
        filesystem=FileSystem("/filesystem_path"),
        outputs=[TaskOutput("/output_1")],
    )

    repo = FakeRepository([task_1, task_2])

    with pytest.raises(
        TaskCollisionError,
        match=(
            "Task collision in filesystem '/filesystem_path' detected on outputs: "
            "'/output_1'"
        ),
    ):
        add_task(task_3, repo, FakeSession())


def test_commit():
    task = Task(owner_id=1, filesystem=FileSystem("."))
    repo = FakeRepository([task])
    session = FakeSession()

    add_task(task, repo, session)

    assert session.committed
