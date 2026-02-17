#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds> <memory_limit_gb>"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
MEM_LIMIT=$4
BASENAME=$(basename "$INPUT_FILE" .graph)

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

source .venv/bin/activate

ulimit -v $(($MEM_LIMIT * 1024 * 1024))

timeout --kill-after=10s $(($TIMEOUT * $K + 1800)) /usr/bin/time -v python3 run_louvain.py --input_file "$INPUT_FILE" --output_file "$BASENAME""_louvain_" --verbose 0 --k "$K" --timeout "$TIMEOUT" > "$BASENAME"_louvain_out.txt 2> "$BASENAME"_louvain_time_mem.txt

STATUS=$?

PYTHON_OUT=$(cat "$BASENAME"_louvain_out.txt)
MAX_MEM=$(cat "$BASENAME"_louvain_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_louvain_out.txt

for i in $(seq 1 $K);
do
    echo -n "louvain,$BASENAME,$i,$MAX_MEM,$STATUS"

    FILE="$BASENAME"_louvain_$((i - 1)).txt
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2 - 1))" '{print $var}')
        MOD=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2))" '{print $var}')
        if [ -f $LABEL_FILE ]; then
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE" "$LABEL_FILE")
            echo ",$TIME,0,""$EVAL_OUT"
        else
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE")
            echo ",$TIME,0,""$EVAL_OUT"
        fi
    else
        echo ""
    fi
done

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_louvain_*.txt