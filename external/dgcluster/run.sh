#!/bin/bash

if [ "$#" -ne 5 ] && [ "$#" -ne 6 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds> <threads> <memory_limit_gb> [<features>]"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
THREADS=$4
MEM_LIMIT=$5
FEATURES=${6:-} # Set to empty if not provided

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

cd DGCluster/

source .venv/bin/activate

export OMP_NUM_THREADS="$THREADS"

ulimit -v $(($MEM_LIMIT * 1024 * 1024))

# Construct the python command
PYTHON_CMD="timeout --kill-after=10s \"$(($TIMEOUT * $K + 1800))\" /usr/bin/time -v python3 main.py --graph_file \"$INPUT_FILE\" --iterations \"$K\" --timelimit \"$TIMEOUT\" --output_path \"$BASENAME""_dgcluster_\""

if [ -n "$FEATURES" ]; then
    PYTHON_CMD="$PYTHON_CMD --feature_file \"$FEATURES\""
fi

# Execute the command
eval "$PYTHON_CMD > \"$BASENAME\"_dgcluster_out.txt 2> \"$BASENAME\"_dgcluster_time_mem.txt"

STATUS=$?

PYTHON_OUT=$(cat "$BASENAME"_dgcluster_out.txt)
MAX_MEM=$(cat "$BASENAME"_dgcluster_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_dgcluster_out.txt

for i in $(seq 1 $K);
do
    echo -n "dgcluster,$BASENAME,$i,$MAX_MEM,$STATUS"

    FILE="$BASENAME"_dgcluster_$((i - 1)).txt
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
rm -rf "$BASENAME"_dgcluster_*.txt