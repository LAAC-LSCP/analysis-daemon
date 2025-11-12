"""
This file contains all helpers and constants related to
the echolalia filesystem, e.g., temp files, log files, outputs
"""

import re
from pathlib import Path
from typing import List, Set, Tuple

from src.config.config import ConfigModel
from src.core.types import UUID


def get_temp_dir(config: ConfigModel) -> Path:
    return config.echolalia_folder / "temp"


def get_output_dir(config: ConfigModel) -> Path:
    return config.echolalia_folder / "outputs"


def get_task_output_dir(config: ConfigModel, task_id: UUID, dataset: str) -> Path:
    return get_output_dir(config) / dataset / str(task_id)


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
            line = line.strip()

            success_match = re.match(r"SUCCESS - Successfully processed - (.+)", line)
            if success_match:
                file_path = success_match.group(1)
                successful_files.add(Path(file_path))
                continue

            error_match = re.match(r"ERROR - Error processing - (.+?) - (.+)", line)
            if error_match:
                file_path = error_match.group(1)
                failed_files.add(Path(file_path))
                continue

    return successful_files, failed_files
