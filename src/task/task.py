from dataclasses import is_dataclass
from typing import Awaitable, Callable, Generic, TypeVar
from uuid import uuid4

from src.types.ids import TaskId, UserId

A = TypeVar("A")


class Task(Generic[A]):
    """
    Represents an asynchronous task with typed arguments and return value.

    This class encapsulates a runner function and its arguments, allowing the task to
    be executed asynchronously. Each task is associated with a unique ID and an owner.

    Type Parameters:
        A: The type of the arguments passed to the runner function. It is recommended
           that 'A' be a dataclass for structured and type-safe arguments.

    Args:
        owner (UserId): The user who owns this task.
        runner (Callable[[A], Awaitable[None]]): An async function that takes arguments
        of type 'A'.
        args (A): The arguments to pass to the runner function.

    Raises:
        TypeError: If 'args' is not a dataclass instance.

    Example:
        @dataclass
        class SumArgs:
            alpha: int
            beta: int

        async def runner(args: SumArgs) -> str:
            return alpha + beta

        sum_numbers = Task(owner, runner, SumArgs(alpha=1, beta=2))
    """

    _owner: UserId
    _id: TaskId
    _args: A
    _runner: Callable[[A], Awaitable[None]]

    def __init__(
        self, owner: UserId, runner: Callable[[A], Awaitable[None]], args: A
    ) -> None:
        if not is_dataclass(args):
            raise TypeError("Task argument `args` must be a dataclass instance.")

        self._id = self._generate_task_id()
        self._owner = owner
        self._runner = runner
        self._args = args  # type: ignore[assignment]

    def _generate_task_id(self) -> TaskId:
        return TaskId(str(uuid4()))

    async def run(self) -> None:
        return await self._runner(self._args)

    @property
    def id(self) -> TaskId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return False

        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
