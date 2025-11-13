import shutil
import subprocess
from pathlib import Path
from typing import Set, Tuple
from uuid import UUID

import click

ECHOLALIA_DIR = Path.home() / "Library" / "Application Support" / "echolalia"
ECHOLALIA_TEMP_DIR = ECHOLALIA_DIR / "temp"


def get_output_dir(echolalia_folder: Path) -> Path:
    return echolalia_folder / "outputs"


def get_task_output_dir(echolalia_folder: Path, task_id: UUID, dataset: str) -> Path:
    return get_output_dir(echolalia_folder) / dataset / str(task_id)


def get_log_file(echolalia_folder: Path, task_id: UUID, dataset: str) -> Path:
    return get_task_output_dir(echolalia_folder, task_id, dataset) / "status.log"


@click.command()
@click.option(
    "--task-id",
    required=True,
    type=click.UUID,
    help="Task id",
)
@click.option(
    "--bash-script",
    required=True,
    type=click.Path(exists=True),
    help="Path to bash script for the task",
)
@click.option(
    "--input-folder",
    required=True,
    type=click.Path(exists=True),
    help="Input folder. Required to reconstruct \
        input folder structure",
)
@click.option(
    "--dataset",
    required=True,
    type=str,
    help="Dataset name",
)
@click.option(
    "--echolalia-folder",
    required=True,
    type=click.Path(exists=False),
    help="Echolalia folder",
)
@click.option(
    "--input",
    "-i",
    required=True,
    multiple=True,
    type=click.Path(exists=True),
    help="Input file (can be used multiple times)",
)
def run_vtc(
    task_id: UUID,
    bash_script: str,
    input_folder: str,
    dataset: str,
    echolalia_folder: str,
    input: Tuple[str],
) -> None:
    bash_script_file, input_dir, echolalia_dir, inputs = _parse_args(
        bash_script, input_folder, echolalia_folder, input
    )

    log_file = get_log_file(Path(echolalia_folder), task_id, dataset)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    working_dir = get_task_output_dir(Path(echolalia_dir), task_id, dataset)

    if not working_dir.exists():
        working_dir.mkdir(parents=True)

    for file in inputs:
        rel_path = file.relative_to(input_dir)

        output_file = (working_dir / rel_path).resolve()

        result = subprocess.run(
            [bash_script_file, str(file), "--device=gpu"],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        status: str
        if result.returncode == 0:
            status = f"SUCCESS - Successfully processed - {file}"

            _move_file(working_dir, file, output_file)
        else:
            status = f"ERROR - Error processing - {file} - {result.stderr}"

        print(status)
        with open(log_file, "a") as f:
            f.write(f"{status}\n")

    return


def _parse_args(
    bash_script: str, input_folder: str, echolalia_folder: str, input: Tuple[str]
) -> Tuple[Path, Path, Path, Set[Path]]:
    return (
        Path(bash_script),
        Path(input_folder),
        Path(echolalia_folder),
        {Path(i) for i in input},
    )


def _move_file(working_dir: Path, input_file: Path, output_file: Path) -> None:
    """
    VTC quirks to bear in mind:

    - VTC puts the output files into the same folder as the present working directory
    - Puts it under the folder "output_voice_type_classifier/[name of input file]"
    - In there you'll find various outputs. We want "all.rttm"
    """
    vtc_output_dir = working_dir / "output_voice_type_classifier" / input_file.stem
    all_rttm = vtc_output_dir / "all.rttm"

    if not all_rttm.exists():
        print(f"WARNING: Expected output file {all_rttm} not found")
        return

    output_file.parent.mkdir(parents=True, exist_ok=True)

    final_output = output_file.with_suffix(".rttm")
    all_rttm.rename(final_output)

    vtc_base_dir = working_dir / "output_voice_type_classifier"
    if vtc_base_dir.exists():
        shutil.rmtree(vtc_base_dir)

    return


if __name__ == "__main__":
    run_vtc()
