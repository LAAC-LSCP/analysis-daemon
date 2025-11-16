#!/bin/bash

# This script mimicks alice's own behaviour
# You pass it an absolute file path
# and it outputs 3 files
# ./diarization_output.rttm
# ./ALICE_output.txt
# ./ALICE_output_utterances.txt
# inside the shell's working directory

INPUT_FILE="$1"
DEVICE=""

if [ -z "$INPUT_FILE" ]; then
    echo "Error: No input file provided"
    exit 1
fi

echo "Processing $INPUT_FILE with ALICE"

touch "diarization_output.rttm"
touch "ALICE_output.txt"  
touch "ALICE_output_utterances.txt"

echo "Created ALICE output files in current directory"
