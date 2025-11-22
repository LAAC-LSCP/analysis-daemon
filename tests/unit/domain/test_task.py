from pathlib import Path

import pytest

from src.config.config import ConfigModel
from src.core.filesystem import get_output_dir
from src.core.response_types import Task as ResponseTypeTask
from src.core.types import UUID, Operation, TaskStatus
from src.domain.commands import CheckTask, CompleteTask, RunTask
from src.domain.events import TaskCompleted, TaskCreated, TaskFailed, TaskStarted
from src.domain.model import Task


@pytest.fixture
def sample_task() -> Task:
    return Task(
        owner_id=UUID("1"),
        dataset="loann_2025",
        status=TaskStatus.PENDING,
        operation=Operation.VTC,
        input_folder=Path("/input/folder"),
        input_files=[Path("/input/folder/file_1.wav")],
    )


def test_task_conversion(sample_task: Task):
    response_type_task = sample_task.to_response_type_task()

    assert response_type_task == ResponseTypeTask(
        datetime=sample_task.created_at,
        owner_id=sample_task.owner_id,
        model_name=sample_task.operation,
        dataset_name=sample_task.dataset,
        status=sample_task.status,
        inputs=[f.file_path for f in sample_task.input_files],
        input_folder=sample_task.input_folder,
        id=sample_task._id,
    )


def test_task_conversion_invertible(sample_task: Task):
    task = sample_task.to_response_type_task().to_model_type_task()

    # Since we overrode equality
    assert task.owner_id == sample_task.owner_id
    assert task.dataset == sample_task.dataset
    assert task.status == sample_task.status
    assert task._id == sample_task._id
    assert task.created_at == sample_task.created_at
    assert task.input_folder == sample_task.input_folder
    assert task.input_files == sample_task.input_files


def test_task_queue(sample_task: Task, config_model: ConfigModel):
    sample_task.queue_task(config_model)

    assert sample_task.status == TaskStatus.PENDING
    assert sample_task.pending
    assert sample_task.events == [TaskCreated(task_id=sample_task._id)]
    assert sample_task.commands == [
        RunTask(
            task_id=sample_task._id,
            dataset=sample_task.dataset,
            operation=sample_task.operation,
            input_folder=sample_task.input_folder,
            input_files=[f.file_path for f in sample_task.input_files],
            echolalia_folder=config_model.echolalia_folder,
        )
    ]


def test_task_run(sample_task: Task, config_model: ConfigModel):
    sample_task.start_run(config_model)

    assert sample_task.status == TaskStatus.RUNNING
    assert sample_task.running
    assert sample_task.events == [TaskStarted(task_id=sample_task._id)]
    assert sample_task.commands == [
        CheckTask(
            task_id=sample_task._id,
            dataset=sample_task.dataset,
            input_folder=sample_task.input_folder,
            output_folder=get_output_dir(config_model),
            input_files=[f.file_path for f in sample_task.input_files],
        )
    ]

    sample_task.events.pop()
    sample_task.commands.pop()
    sample_task.end_run()

    assert sample_task.commands == [CompleteTask(task_id=sample_task._id)]


def test_task_complete(sample_task: Task):
    sample_task.mark_completed()

    assert sample_task.status == TaskStatus.COMPLETED
    assert sample_task.completed
    assert sample_task.events == [TaskCompleted(task_id=sample_task._id)]
    assert sample_task.commands == []


def test_task_fail(sample_task: Task):
    e = Exception("test")
    sample_task.mark_failed(e)

    assert sample_task.status == TaskStatus.FAILED
    assert sample_task.failed
    assert sample_task.events == [
        TaskFailed(
            task_id=sample_task._id,
            stack_trace=f"Task with id {sample_task._id} failed: {repr(e)}",
        )
    ]
    assert sample_task.commands == []
