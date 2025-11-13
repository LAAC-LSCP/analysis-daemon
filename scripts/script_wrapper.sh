#!/bin/bash

# I would typically avoid a bash script like this in favor of Python,
# as bash scripts are a pain to maintain and test
# but we need to activate the Conda environment before running the script
# (and therefore also pass in all the relevant arguments)
# therefore this is the way we'll go

TASK_ID=""
PYTHON_SCRIPT=""
BASH_SCRIPT=""
DATASET=""
INPUT_FOLDER=""
ECHOLALIA_FOLDER=""
CONDA_SRC=""
ENV_NAME=""
INPUT_FILES=()

# Parse arguments manually
# Note that the order is clearly important, and that input files need to come one
# after the other
while [[ $# -gt 0 ]]; do
  case $1 in
    --task-id)
      TASK_ID="$2"
      shift 2
      ;;
    --python-script)
      PYTHON_SCRIPT="$2"
      shift 2
      ;;
    --bash-script)
      BASH_SCRIPT="$2"
      shift 2
      ;;
    --dataset)
      DATASET="$2"
      shift 2
      ;;
    --input-folder)
      INPUT_FOLDER="$2"
      shift 2
      ;;
    --echolalia-folder)
      ECHOLALIA_FOLDER="$2"
      shift 2
      ;;
    --conda-src)
      CONDA_SRC="$2"
      shift 2
      ;;
    --env-name)
      ENV_NAME="$2"
      shift 2
      ;;
    -i|--input)
      INPUT_FILES+=("$2")
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--task-id task id] [--python-script path] [--bash-script path] [--dataset name] [--input-folder path] [--echolalia-folder path] [--conda-src path] [--env-name name] [-i input file]"
      echo "Use -i multiple times for multiple input files"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Load conda environment
source "$CONDA_SRC"
conda activate "$ENV_NAME"

cmd=(python3 "$PYTHON_SCRIPT" --task-id "$TASK_ID" --dataset "$DATASET" --input-folder "$INPUT_FOLDER" --echolalia-folder "$ECHOLALIA_FOLDER" --bash-script "$BASH_SCRIPT")

for file in "${INPUT_FILES[@]}"; do
  cmd+=(-i "$file")
done

"${cmd[@]}"