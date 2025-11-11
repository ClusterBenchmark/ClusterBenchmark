#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds> <threads>"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
THREADS=$4
BASENAME=$(basename "$INPUT_FILE" .graph)

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

source .venv/bin/activate

export OMP_NUM_THREADS="$THREADS"

/usr/bin/time -v python3 run_infomap.py --input_file "$INPUT_FILE" --output_file "$BASENAME""_infomap_" --verbose 0 --k "$K" --timeout "$TIMEOUT" > "$BASENAME"_infomap_out.txt 2> "$BASENAME"_infomap_time_mem.txt

PYTHON_OUT=$(cat "$BASENAME"_infomap_out.txt)
MAX_MEM=$(cat "$BASENAME"_infomap_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_infomap_out.txt

echo -n "$BASENAME,$MAX_MEM"

for i in $(seq 1 $K);
do
    FILE="$BASENAME"_infomap_$((i - 1)).txt
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2 - 1))" '{print $var}')
        MOD=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2))" '{print $var}')
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE")
        EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
        EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
        EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')

        echo -n ",$TIME,$MOD,$EVAL_MOD,$EVAL_N,$EVAL_CC"
    else
        echo -n ",tle,tle,tle,tle,tle"
    fi
done

echo ""

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_infomap_*.txt