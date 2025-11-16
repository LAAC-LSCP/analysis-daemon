"""
Note: ALICE uses Python 3.6.7. and it can't really be upgraded

We use some older syntax here.
"""

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
def run_alice(
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

    log_file = get_log_file(echolalia_dir, task_id, dataset)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    output_dir = get_task_output_dir(echolalia_dir, task_id, dataset)

    # ALICE has some quirk where the working dir MUST be the ALICE path
    # or else it can't run
    working_dir = bash_script_file.parent

    for file in inputs:
        rel_path = file.relative_to(input_dir)

        output_file = (output_dir / rel_path).resolve()

        result = subprocess.run(
            [str(bash_script_file), str(file), "--device=gpu"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=working_dir,
        )

        status: str
        if result.returncode == 0:
            status = "SUCCESS - Successfully processed - {}".format(file)

            _move_file(working_dir, output_file)
        else:
            status = "ERROR - Error processing - {} - {}".format(file, result.stderr)

        with open(log_file, "a") as f:
            f.write("{}\n".format(status))

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


def _move_file(working_dir: Path, output_file: Path) -> None:
    """
    ALICE quirks to bear in mind:

    - ALICE puts everything in the CWD
    - The CWD must be where the ALICE script is
    - The outputs are ALICE_output.txt, ALICE_output_utterances.txt
    and diarization_output.rttm

    This means we create two files in the output folder:
    [name_of_output].txt
    [name_of_output]_sum.txt
    """
    diarization_file = working_dir / "diarization_output.rttm"
    if diarization_file.exists():
        diarization_file.unlink()

    sum_output = working_dir / "ALICE_output.txt"
    utterances_output = working_dir / "ALICE_output_utterances.txt"

    if not sum_output.exists():
        print("WARNING: Expected output file {} not found".format(str(sum_output)))

    if not utterances_output.exists():
        print(
            "WARNING: Expected output file {} not found".format(str(utterances_output))
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    if sum_output.exists():
        sum_target = output_file.parent / (output_file.stem + "_sum.txt")
        sum_output.rename(sum_target)

    if utterances_output.exists():
        utterances_target = output_file.parent / (output_file.stem + ".txt")
        utterances_output.rename(utterances_target)

    return


if __name__ == "__main__":
    run_alice()
