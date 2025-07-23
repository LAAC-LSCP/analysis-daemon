from typing import Awaitable, overload

from src.task import Task
from src.types.ids import UserId
from src.types.task import LogTaskName, TaskArgs, TaskType
from src.types.tasks.log import LogArgs


class TaskFactory:
    """
    Factory class to create Task instances based on task type and arguments.

    This factory centralizes the creation logic for different types of tasks.

    Example:
        factory = TaskFactory()
        task = factory.create(
            task_type="log",
            owner="12345",
            args=LogArgs(
                text=["Hello", "World"],
            ),
        )
    """

    def __init__(self) -> None:
        return

    # Uncomment type comment when more overloads are added
    @overload   # type: ignore[misc]
    def create(
        self, task_type: LogTaskName, owner: UserId, args: LogArgs
    ) -> Task[LogArgs]: ...

    def create(self, task_type: TaskType, owner: UserId, args: TaskArgs) -> Task:
        if task_type == "log":
            return self._create_logging_task(owner, args)

        raise ValueError(f"Unknown task type: {task_type}")

    def _create_logging_task(self, owner: UserId, args: LogArgs) -> Task[LogArgs]:
        async def runner(args: LogArgs) -> None:
            for line in args.text:
                print(line)

            return None

        return Task(owner, runner, args)
