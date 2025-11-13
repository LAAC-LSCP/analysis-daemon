#!/bin/bash

# This script mimicks vtc's own behaviour
# You pass it an absolute file path
# and it outputs a file "filename/output_voice_type_classifier/all.rttm"
# inside the shell's working directory

INPUT_FILE="$1"
DEVICE=""

if [ -z "$INPUT_FILE" ]; then
    echo "Error: No input file provided"
    exit 1
fi

FILENAME=$(basename "$INPUT_FILE" .wav)

OUTPUT_DIR="output_voice_type_classifier/$FILENAME"
mkdir -p "$OUTPUT_DIR"

touch "$OUTPUT_DIR/all.rttm"
