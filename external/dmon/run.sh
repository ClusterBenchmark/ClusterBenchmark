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

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# If the feature file path is relative, make it absolute.
if [[ -n "$FEATURES" && "$FEATURES" != /* ]]; then
    FEATURES="$(pwd)/$FEATURES"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

cd google-research/

source .venv/bin/activate

export OMP_NUM_THREADS="$THREADS"

ulimit -v $(($MEM_LIMIT * 1024 * 1024))

# Construct the python command
PYTHON_CMD="timeout --kill-after=10s \"$(($TIMEOUT * $K + 600))\" /usr/bin/time -v python3 -m graph_embedding.dmon.train_metis --graph_path=\"$INPUT_FILE\" --n_clusters=\"$C\" --n_runs=\"$K\" --n_epochs=1000 --dropout_rate=0.5 --timeout=\"$TIMEOUT\" --n_threads=\"$THREADS\" --output_path=\"$BASENAME""_dmon_\""

if [ -n "$FEATURES" ]; then
    PYTHON_CMD="$PYTHON_CMD --features_path=\"$FEATURES\""
fi

# Execute the command
eval "$PYTHON_CMD > \"$BASENAME\"_dmon_out.txt 2> \"$BASENAME\"_dmon_time_mem.txt"

STATUS=$?

PYTHON_OUT=$(cat "$BASENAME"_dmon_out.txt)
MAX_MEM=$(cat "$BASENAME"_dmon_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_dmon_out.txt

for i in $(seq 1 $K);
do
    echo -n "dmon,$BASENAME,$i,$MAX_MEM,$STATUS"

    FILE="$BASENAME"_dmon_$((i - 1)).txt
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 3 - 2))" '{print $var}')
        IT=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 3 - 1))" '{print $var}')

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
rm -rf "$BASENAME"_dmon_*.txt