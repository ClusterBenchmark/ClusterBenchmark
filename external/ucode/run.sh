#!/bin/bash

if [ "$#" -ne 5 ] && [ "$#" -ne 6 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds> <threads> <c> [<features>]"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
THREADS=$4
C=$5
FEATURES=${6:-} # Set to empty if not provided

BASENAME=$(basename "$INPUT_FILE" .graph)

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

cd UCODE/

source .venv/bin/activate

export OMP_NUM_THREADS="$THREADS"

# Construct the python command
PYTHON_CMD="/usr/bin/time -v python3 main.py --metis_file=\"$INPUT_FILE\" --K \"$C\" --it \"$K\" --timeout=\"$TIMEOUT\" --output_file \"$BASENAME""_ucode\""

if [ -n "$FEATURES" ]; then
    PYTHON_CMD="$PYTHON_CMD --features_file \"$FEATURES\""
fi

# Execute the command
eval "$PYTHON_CMD > \"$BASENAME\"_ucode_out.txt 2> \"$BASENAME\"_ucode_time_mem.txt"

PYTHON_OUT=$(cat "$BASENAME"_ucode_out.txt)
MAX_MEM=$(cat "$BASENAME"_ucode_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_ucode_out.txt

for i in $(seq 1 $K);
do
    echo -n "$BASENAME,$i,$MAX_MEM"

    FILE="$BASENAME"_ucode_$((i - 1)).txt
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2 - 1))" '{print $var}')
        IT=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2))" '{print $var}')

        if [ -f $LABEL_FILE ]; then
            EVAL_OUT=$(../../../EVAL "$INPUT_FILE" "$FILE" "$LABEL_FILE")
            echo ",$TIME,$IT,""$EVAL_OUT"
        else
            EVAL_OUT=$(../../../EVAL "$INPUT_FILE" "$FILE")
            echo ",$TIME,$IT,""$EVAL_OUT"
        fi
    else
        echo ""
    fi
done

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_ucode_*.txt