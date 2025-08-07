from pathlib import Path
from typing import Set


class TaskCollisionError(Exception):
    """Raised when a task would (potentially) conflict with a running task"""

    def __init__(self, filesystem: Path, conflicting_outputs: Set[Path]):
        self.filesystem = filesystem
        self.conflicting_outputs = conflicting_outputs

        output_paths = ", ".join(f"'{str(output)}'" for output in conflicting_outputs)

        super().__init__(
            (
                f"Task collision in filesystem '{str(filesystem)}' detected "
                f"on outputs: {output_paths}"
            )
        )
