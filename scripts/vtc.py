from pathlib import Path
import shutil
import subprocess
from typing import Set, Tuple
import click


ECHOLALIA_DIR = Path.home() / "Library" / "Application Support" / "echolalia"
ECHOLALIA_TEMP_DIR = ECHOLALIA_DIR / "temp"


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
    "--output-folder",
    required=True,
    type=click.Path(exists=False),
    help="Output folder",
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
    task_id: str,
    bash_script: str,
    input_folder: str,
    output_folder: str,
    input: Tuple[str],
) -> None:
    bash_script_file, input_dir, output_dir, inputs = _parse_args(
        bash_script, input_folder, output_folder, input
    )

    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    working_dir = ECHOLALIA_TEMP_DIR / str(task_id)

    if not working_dir.exists():
        working_dir.mkdir(parents=True)

    for file in inputs:
        rel_path = file.relative_to(input_dir)

        output_file = (output_dir / rel_path).resolve()

        result = subprocess.run(
            [bash_script_file, str(file), "--device=gpu"],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        if result.returncode == 0:
            print(f"SUCCESS: Successfully processed {file}")

            _move_file(working_dir, file, output_file)

        if result.returncode != 0:
            print(f"ERROR: Error processing {file}: {result.stderr}")

    return


def _parse_args(
    bash_script: str, input_folder: str, output_folder: str, input: Tuple[str]
) -> Tuple[Path, Path, Path, Set[Path]]:
    return (
        Path(bash_script),
        Path(input_folder),
        Path(output_folder),
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
