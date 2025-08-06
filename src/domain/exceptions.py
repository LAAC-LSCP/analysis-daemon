from typing import Set

from src.domain.model import FileSystem, TaskOutput


class TaskCollisionError(Exception):
    """Raised when a task would (potentially) conflict with a running task"""

    def __init__(self, filesystem: FileSystem, conflicting_outputs: Set[TaskOutput]):
        self.filesystem = filesystem
        self.conflicting_outputs = conflicting_outputs

        output_paths = ", ".join(f"'{str(output)}'" for output in conflicting_outputs)

        super().__init__(
            (
                f"Task collision in filesystem '{filesystem.root_abs_path}' detected "
                f"on outputs: {output_paths}"
            )
        )
