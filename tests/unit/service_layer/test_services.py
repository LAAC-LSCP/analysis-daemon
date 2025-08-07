from pathlib import Path

import pytest

from src.service_layer.services import TaskCollisionError, add_task
from tests.unit.service_layer.fakes import FakeRepository, FakeSession, TaskArgs


def test_adding_returns_task_id():
    repo = FakeRepository()

    result = add_task(
        owner_id=1, filesystem=Path("/path1"), repo=repo, session=FakeSession()
    )

    assert result == 1


def test_collisions_on_same_file_system():
    repo = FakeRepository.for_tasks(
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
            repo=repo,
            session=FakeSession(),
        )


def test_commit():
    repo = FakeRepository([])
    session = FakeSession()

    add_task(owner_id=1, filesystem=Path("."), repo=repo, session=session)

    assert session.committed
