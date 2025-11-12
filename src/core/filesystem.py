"""
This file contains all helpers and constants related to
the echolalia filesystem, e.g., temp files, log files, outputs
"""

from pathlib import Path
from typing import List, Set, Tuple

from src.config.config import ConfigModel
from src.core.types import UUID


def get_temp_dir(config: ConfigModel) -> Path:
    return config.echolalia_folder / "temp"


def get_output_dir(config: ConfigModel) -> Path:
    return config.echolalia_folder / "outputs"


def get_task_output_dir(config: ConfigModel, task_id: UUID, dataset: str) -> Path:
    return config.echolalia_folder / dataset / str(task_id)


def get_log_file(config: ConfigModel, task_id: UUID, dataset: str) -> Path:
    return get_task_output_dir(config, task_id, dataset) / "status.log"


def log_file_info(log_file: Path) -> Tuple[Set[Path], Set[Path]]:
    successful_files: Set[Path] = set()
    failed_files: Set[Path] = set()

    if not log_file.exists():
        return successful_files, failed_files

    with open(log_file, "r") as f:
        lines: List[str] = f.readlines()

        for line in lines:
            status_string, _, file_path = [part.strip() for part in line.split("-")][:3]

            if status_string == "SUCCESS":
                successful_files.add(Path(file_path))
                continue

            if status_string == "ERROR":
                failed_files.add(Path(file_path))
                continue

    return successful_files, failed_files
