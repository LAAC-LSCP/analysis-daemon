from pathlib import Path
from typing import List

from click.testing import CliRunner, Result

from scripts.alice import run_alice
from src.config.config import ConfigModel


def test_run_alice_exit_code(config_model: ConfigModel, config_path: Path) -> None:
    echolalia_dir = config_model.echolalia_folder
    filesystem_root = config_path.parent

    result = _run_alice(echolalia_dir, filesystem_root)

    assert result.exit_code == 0


def test_run_alice_outputs(config_model: ConfigModel, config_path: Path) -> None:
    echolalia_dir = config_model.echolalia_folder
    filesystem_root = config_path.parent

    _run_alice(echolalia_dir, filesystem_root)

    input_folder = (
        filesystem_root / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )
    output_folder = (
        echolalia_dir
        / "outputs"
        / "loann_2025"
        / "32299d40-ea8c-4d9b-941e-690389ad8f34"
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
        output_folder / "empty_wav.txt",
        output_folder / "empty_wav_sum.txt",
        output_folder / "folder_1" / "empty_wav_1_1.txt",
        output_folder / "folder_1" / "empty_wav_1_1_sum.txt",
        output_folder / "folder_1" / "folder_3" / "empty_wav_1_3_1.txt",
        output_folder / "folder_1" / "folder_3" / "empty_wav_1_3_1_sum.txt",
        output_folder / "folder_1" / "folder_3" / "empty_wav_1_3_2.txt",
        output_folder / "folder_1" / "folder_3" / "empty_wav_1_3_2_sum.txt",
    ]

    assert files == set(outputs)

    lines: List[str] = []
    with open(status_log, "r") as f:
        lines = f.readlines()

    assert set(lines) == set(
        [f"SUCCESS - Successfully processed - {str(f)}\n" for f in inputs]
    )


def _run_alice(echolalia_dir: Path, filesystem_root: Path) -> Result:
    cli_runner = CliRunner()

    input_dir = (
        filesystem_root / "datasets" / "loann_2025" / "recordings" / "example_inputs"
    )

    input_1 = input_dir / "empty_wav.wav"
    input_2 = input_dir / "folder_1" / "empty_wav_1_1.wav"
    input_3 = input_dir / "folder_1" / "folder_3" / "empty_wav_1_3_1.wav"
    input_4 = input_dir / "folder_1" / "folder_3" / "empty_wav_1_3_2.wav"

    return cli_runner.invoke(
        run_alice,
        [
            "--task-id",
            "32299d40-ea8c-4d9b-941e-690389ad8f34",
            "--bash-script",
            str(filesystem_root / "apply_alice.sh"),
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
