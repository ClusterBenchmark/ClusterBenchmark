#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path_to_graph_file> <k>"
    exit 1
fi

INPUT_FILE=$1
K=$2
BASENAME=$(basename "$INPUT_FILE" .graph)

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

source .venv/bin/activate

export OMP_NUM_THREADS=4

timeout -s SIGTERM 3600s python3 gnns.py "$INPUT_FILE" "$BASENAME" "$K" 2> /dev/null > "$BASENAME"_gnns_out.txt

PYTHON_OUT=$(cat "$BASENAME"_gnns_out.txt)

echo -n "$BASENAME"

for i in $(seq 1 $K);
do
    FILE="$BASENAME"_gnns_$((i - 1)).txt
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i))" '{print $var}')
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE")
        EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
        EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
        EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')

        echo -n ",$TIME,$EVAL_MOD,$EVAL_N,$EVAL_CC"
    else
        echo -n ",tle,tle,tle,tle"
    fi
done

echo ""

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_gnns_*.txt