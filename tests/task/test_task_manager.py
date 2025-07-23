import pytest

from src.task import TaskManager
from src.types.ids import TaskId, UserId
from src.types.tasks.log import LogArgs, LogTaskName


@pytest.fixture(scope="module")
def task_manager() -> TaskManager:
    return TaskManager()


def test_task_manager_registers_tasks(task_manager: TaskManager):
    user: UserId = UserId("12345")
    task_type: LogTaskName = "log"
    task_1: TaskId = task_manager.add_task(task_type, user, LogArgs(text=["Hello World!"]))
    task_2: TaskId = task_manager.add_task(task_type, user, LogArgs(text=["Hello World again!"]))

    assert task_1 in task_manager
    assert task_2 in task_manager
