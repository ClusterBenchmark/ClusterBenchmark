#!/bin/bash

if [ "$#" -ne 6 ] && [ "$#" -ne 7 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds> <threads> <c> <memory_limit_gb> [<features>]"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
THREADS=$4
C=$5
MEM_LIMIT=$6
FEATURES=${7:-} # Set to empty if not provided

BASENAME=$(basename "$INPUT_FILE" .graph)

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

cd MAGI/

source .venv/bin/activate

ulimit -v $(($MEM_LIMIT * 1024 * 1024))

export OMP_NUM_THREADS="$THREADS"

# Construct the python command
PYTHON_CMD="timeout --kill-after=10s \"$(($TIMEOUT * $K + 1800))\" /usr/bin/time -v python3 train_sage.py --graph_file \"$INPUT_FILE\" --output_path \"$BASENAME\"_magi_ --iterations \"$K\" --n_clusters \"$C\" --timelimit \"$TIMEOUT\""

if [ -n "$FEATURES" ]; then
    PYTHON_CMD="$PYTHON_CMD --feature_file \"$FEATURES\""
fi

# Execute the command
eval "$PYTHON_CMD > \"$BASENAME\"_magi_out.txt 2> \"$BASENAME\"_magi_time_mem.txt"

STATUS=$?

PYTHON_OUT=$(cat "$BASENAME"_magi_out.txt)
MAX_MEM=$(cat "$BASENAME"_magi_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_magi_out.txt

for i in $(seq 1 $K);
do
    echo -n "magi,$BASENAME,$i,$MAX_MEM,$STATUS"

    FILE="$BASENAME"_magi_$((i - 1)).txt
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
rm -rf "$BASENAME"_magi_*.txt