"""
Many of the helpers are duplicated from the source code
But since people won't be copying the entire source code,
we need to instead have tests to make sure that changes in the
source are reflected in the scripts
"""

from uuid import UUID

from scripts.helpers import get_log_file as scripts_get_log_file
from scripts.helpers import get_output_dir as scripts_get_output_dir
from scripts.helpers import get_task_output_dir as scripts_get_task_output_dir
from scripts.helpers import get_temp_dir as scripts_get_temp_dir
from src.config.config import ConfigModel
from src.core.filesystem import get_log_file as core_get_log_file
from src.core.filesystem import get_output_dir as core_get_output_dir
from src.core.filesystem import get_task_output_dir as core_get_task_output_dir
from src.core.filesystem import get_temp_dir as core_get_temp_dir
from src.core.types import UUID as CoreUUID


def test_get_temp_dir(config_model: ConfigModel):
    assert core_get_temp_dir(config_model) == scripts_get_temp_dir(
        config_model.echolalia_folder
    )


def test_get_output_dir(config_model: ConfigModel):
    assert core_get_output_dir(config_model) == scripts_get_output_dir(
        config_model.echolalia_folder
    )


def test_get_task_output_dir(config_model: ConfigModel):
    assert core_get_task_output_dir(
        config_model, CoreUUID("750a8e9b-c538-4473-a483-faa329b9246d"), "loann_2025"
    ) == scripts_get_task_output_dir(
        config_model.echolalia_folder,
        UUID("750a8e9b-c538-4473-a483-faa329b9246d"),
        "loann_2025",
    )


def test_get_log_file(config_model: ConfigModel):
    assert core_get_log_file(
        config_model, CoreUUID("750a8e9b-c538-4473-a483-faa329b9246d"), "loann_2025"
    ) == scripts_get_log_file(
        config_model.echolalia_folder,
        UUID("750a8e9b-c538-4473-a483-faa329b9246d"),
        "loann_2025",
    )
