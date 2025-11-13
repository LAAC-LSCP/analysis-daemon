from pathlib import Path
from typing import List

from click.testing import CliRunner, Result

from scripts.vtc import run_vtc
from src.config.config import ConfigModel


def test_run_vtc_exit_code(config_model: ConfigModel, config_path: Path) -> None:
    echolalia_dir = config_model.echolalia_folder
    filesystem_root = config_path.parent

    result = _run_vtc(echolalia_dir, filesystem_root)

    assert result.exit_code == 0


def test_run_vtc_outputs(config_model: ConfigModel, config_path: Path) -> None:
    echolalia_dir = config_model.echolalia_folder
    filesystem_root = config_path.parent

    _run_vtc(echolalia_dir, filesystem_root)

    input_folder = (
        filesystem_root / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )
    output_folder = (
        echolalia_dir
        / "outputs"
        / "loann_2025"
        / "750a8e9b-c538-4473-a483-faa329b9246d"
    )

    assert (output_folder).exists()
    files = set([f for f in output_folder.rglob("**") if f.is_file()])
    status_log = output_folder / "status.log"

    inputs = [
        input_folder / "empty_wav.wav",
        input_folder / "folder_1" / "empty_wav_1_1.wav",
        input_folder / "folder_1" / "folder_3" / "empty_wav_1_3_1.wav",
        input_folder / "folder_1" / "folder_3" / "empty_wav_1_3_2.wav",
    ]

    outputs = [
        status_log,
        output_folder / "empty_wav.rttm",
        output_folder / "folder_1" / "empty_wav_1_1.rttm",
        output_folder / "folder_1" / "folder_3" / "empty_wav_1_3_1.rttm",
        output_folder / "folder_1" / "folder_3" / "empty_wav_1_3_2.rttm",
    ]

    assert files == set(outputs)

    lines: List[str] = []
    with open(status_log, "r") as f:
        lines = f.readlines()

    assert set(lines) == set(
        [f"SUCCESS - Successfully processed - {str(f)}\n" for f in inputs]
    )


def _run_vtc(echolalia_dir: Path, filesystem_root: Path) -> Result:
    cli_runner = CliRunner()

    input_dir = (
        filesystem_root / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )

    input_1 = input_dir / "empty_wav.wav"
    input_2 = input_dir / "folder_1" / "empty_wav_1_1.wav"
    input_3 = input_dir / "folder_1" / "folder_3" / "empty_wav_1_3_1.wav"
    input_4 = input_dir / "folder_1" / "folder_3" / "empty_wav_1_3_2.wav"

    return cli_runner.invoke(
        run_vtc,
        [
            "--task-id",
            "750a8e9b-c538-4473-a483-faa329b9246d",
            "--bash-script",
            str(filesystem_root / "apply_vtc.sh"),
            "--input-folder",
            str(input_dir),
            "--dataset",
            "loann_2025",
            "--echolalia-folder",
            str(echolalia_dir),
            "-i",
            str(input_1),
            "-i",
            str(input_2),
            "-i",
            str(input_3),
            "-i",
            str(input_4),
        ],
    )
