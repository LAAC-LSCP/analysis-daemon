"""
More or less copied from analysis-daemon source filesystems.py
"""

from pathlib import Path
from uuid import UUID


def get_temp_dir(echolalia_folder: Path) -> Path:
    return echolalia_folder / "temp"


def get_output_dir(echolalia_folder: Path) -> Path:
    return echolalia_folder / "outputs"


def get_task_output_dir(echolalia_folder: Path, task_id: UUID, dataset: str) -> Path:
    return get_output_dir(echolalia_folder) / dataset / str(task_id)


def get_log_file(echolalia_folder: Path, task_id: UUID, dataset: str) -> Path:
    return get_task_output_dir(echolalia_folder, task_id, dataset) / "status.log"
