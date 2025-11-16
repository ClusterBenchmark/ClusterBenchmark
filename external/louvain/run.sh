#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds>"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
BASENAME=$(basename "$INPUT_FILE" .graph)

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

source .venv/bin/activate

/usr/bin/time -v python3 run_louvain.py --input_file "$INPUT_FILE" --output_file "$BASENAME""_louvain_" --verbose 0 --k "$K" --timeout "$TIMEOUT" > "$BASENAME"_louvain_out.txt 2> "$BASENAME"_louvain_time_mem.txt

PYTHON_OUT=$(cat "$BASENAME"_louvain_out.txt)
MAX_MEM=$(cat "$BASENAME"_louvain_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_louvain_out.txt

for i in $(seq 1 $K);
do
    echo -n "$BASENAME,$i,$MAX_MEM"

    FILE="$BASENAME"_louvain_$((i - 1)).txt
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2 - 1))" '{print $var}')
        MOD=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2))" '{print $var}')

        if [ -f $LABEL_FILE ]; then
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE" "$LABEL_FILE")
            EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
            EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
            EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
            EVAL_F1=$(echo "$EVAL_OUT" | awk -F',' '{print $7}')
            EVAL_AC=$(echo "$EVAL_OUT" | awk -F',' '{print $8}')
            EVAL_TP=$(echo "$EVAL_OUT" | awk -F',' '{print $9}')
            EVAL_FP=$(echo "$EVAL_OUT" | awk -F',' '{print $10}')
            EVAL_TN=$(echo "$EVAL_OUT" | awk -F',' '{print $11}')
            EVAL_FN=$(echo "$EVAL_OUT" | awk -F',' '{print $12}')
            
            echo ",$TIME,$MOD,$EVAL_MOD,$EVAL_N,$EVAL_CC,$EVAL_F1,$EVAL_AC,$EVAL_TP,$EVAL_FP,$EVAL_TN,$EVAL_FN"
        else
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE")
            EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
            EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
            EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
            
            echo ",$TIME,$MOD,$EVAL_MOD,$EVAL_N,$EVAL_CC"
        fi
    else
        if [ -f $LABEL_FILE ]; then
            echo ",tle,tle,tle,tle,tle,tle,tle,tle,tle,tle,tle"
        else
            echo ",tle,tle,tle,tle,tle"
        fi
    fi
done

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_louvain_*.txt