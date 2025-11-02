from pathlib import Path

from src.core.types import UUID, Operation, TaskStatus


class CoreException(Exception):
    """Base exception for core errors."""

    pass


class NoFileSystemWithPath(CoreException):
    """Raised when a path is not associated with any filesystem."""

    def __init__(self, path: Path):
        self.path = path
        super().__init__(
            f"Filesystem path '{path}' does not exist in configured filesystems."
        )


class NoFileSystemWithDataset(CoreException):
    """Raised when a dataset name is not associated with any filesystem."""

    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        super().__init__(
            f"Dataset '{dataset_name}' does not exist in configured filesystems."
        )


class NoScriptWithOperation(CoreException):
    """Raised when there is no script found for a given operation"""

    def __init__(self, operation: Operation):
        self.operation = operation
        super().__init__(
            f"No script found in configuration with operation {operation.value}"
        )


class ScriptNameNotInDataset(CoreException):
    """Raised when a script name cannot be found in a filesystem."""

    def __init__(self, script_name: str, dataset_name: str):
        self.script_name = script_name
        self.dataset_name = dataset_name
        super().__init__(
            f"Script path '{script_name} does not exist' \
            in dataset '{dataset_name}'."
        )


class ScriptPathDoesNotExistInDataset(CoreException):
    """Raised when a script path does not exist in the given dataset."""

    def __init__(self, script_path: Path, dataset_name: str):
        self.script_path = script_path
        self.dataset_name = dataset_name
        super().__init__(
            f"Script path '{script_path}' does not exist \
            in dataset '{dataset_name}'."
        )


class InValidTaskStatus(CoreException):
    """Raised when trying to pass an invalid task status"""

    def __init__(self, task_status: str):
        self.task_status = task_status
        super().__init__(
            f"task_status '{task_status}' not in {str([s.value for s in TaskStatus])}"
        )


class TaskNotFound(CoreException):
    """Raised when a task is not found"""

    def __init__(self, task_id: UUID):
        self._task_id = task_id
        super().__init__(f"task with id {task_id}' could not be found")
