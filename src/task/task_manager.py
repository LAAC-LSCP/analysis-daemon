from typing import Union, overload

from src.task import Task
from src.task.task_factory import TaskFactory
from src.types.ids import TaskId, UserId
from src.types.task import LogArgs, LogTaskName, TaskArgs, TaskType


class TaskManager:
    """
    Manages lifecycle and execution of asynchronous tasks.

    The TaskManager is responsible for creating, tracking, and managing
    tasks within the application. It maintains an internal set of active
    tasks and allows adding new tasks via a factory.

    Example:
        manager = TaskManager()
        task_id = manager.add_task(
            task_type="log",
            user="12345",
            args=LogArgs(
                text=["Hello World!"]
            ),
        )
        if task_id in manager.get_task_ids():
            print("Task registered.")
    """

    _tasks: set[Task]
    _task_factory: TaskFactory

    def __init__(self) -> None:
        self._tasks = set()
        self._task_factory = TaskFactory()

    # Uncomment type comment when more overloads are added
    @overload   # type: ignore[misc]
    def add_task(
        self, task_type: LogTaskName, owner: UserId, args: LogArgs
    ) -> TaskId: ...

    def add_task(self, task_type: TaskType, owner: UserId, args: TaskArgs) -> TaskId:
        task: Task = self._task_factory.create(
            task_type=task_type, owner=owner, args=args
        )
        self._tasks.add(task)

        return task.id

    def stop_task(self, task_id: TaskId) -> None:
        raise NotImplementedError

    def kill_task(self, task_id: TaskId) -> None:
        raise NotImplementedError

    def get_task_ids(self) -> list[TaskId]:
        return [task.id for task in self._tasks]

    def __contains__(self, task: Union[Task, TaskId]) -> bool:
        if isinstance(task, Task):
            return task in self._tasks
        elif isinstance(
            task, str
        ):  # TaskId. NewType does not allow runtime type checking
            return task in self.get_task_ids()

        raise TypeError("Expected argument `task` to be type `Task` or `TaskId`")
