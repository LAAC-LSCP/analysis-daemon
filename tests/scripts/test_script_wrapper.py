from pathlib import Path

import pytest

from src.config.config import ConfigModel
from src.core.types import UUID, Operation
from src.domain.commands import RunTask
from src.service_layer.handlers.command_handlers import _run_task


@pytest.mark.asyncio
async def test_script_wrapper_on_empty_scripts(
    config_model: ConfigModel, config_path: Path
):
    """Bit strange perhaps to import command info but it's easier
    to do things this way, and it tests both the run task and the wrapper
    simultaneously"""
    filesystem_root = config_path.parent
    input_dir = (
        filesystem_root / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )

    input_1 = input_dir / "empty_wav.wav"
    input_2 = input_dir / "folder_1" / "empty_wav_1_1.wav"

    task_id = UUID("750a8e9b-c538-4473-a483-faa329b9246d")
    dataset = "loann_2025"

    command = RunTask(
        task_id=task_id,
        dataset=dataset,
        operation=Operation.VTC,
        input_folder=input_dir,
        input_files=[input_1, input_2],
        echolalia_folder=config_model.echolalia_folder,
    )

    await _run_task(command, config_model)

    assert True


@pytest.mark.asyncio
async def test_script_wrapper_on_vtc(config_model: ConfigModel, config_path: Path):
    """Bit strange perhaps to import command info but it's easier
    to do things this way, and it tests both the run task and the wrapper
    simultaneously"""
    filesystem_root = config_path.parent
    input_dir = (
        filesystem_root / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )

    input_1 = input_dir / "empty_wav.wav"
    input_2 = input_dir / "folder_1" / "empty_wav_1_1.wav"

    task_id = UUID("222a8e9b-c538-4473-a483-faa329b9246d")
    dataset = "loann_2025"

    command = RunTask(
        task_id=task_id,
        dataset=dataset,
        operation=Operation.VTC,
        input_folder=input_dir,
        input_files=[input_1, input_2],
        echolalia_folder=config_model.echolalia_folder,
    )
    await _run_task(command, config_model)

    output_folder = (
        config_model.echolalia_folder
        / "outputs"
        / "loann_2025"
        / "222a8e9b-c538-4473-a483-faa329b9246d"
    )

    assert (output_folder).exists()
    files = set([f for f in output_folder.rglob("**") if f.is_file()])

    assert files == set(
        [
            output_folder / "status.log",
            output_folder / "empty_wav.rttm",
            output_folder / "folder_1" / "empty_wav_1_1.rttm",
        ]
    )
