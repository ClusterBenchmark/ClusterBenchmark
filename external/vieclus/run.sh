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

for i in $(seq 1 $K);
do
    TIME=$(/usr/bin/time -v mpirun -n $THREADS ./vieclus "$INPUT_FILE" --time_limit="$TIMEOUT" --seed="$i" --output_filename="$BASENAME"_clustering.txt 2> "$BASENAME"_vieclus_time_mem.txt | grep 'Best solution found after' | awk '{print $5}')
    MAX_MEM=$(cat "$BASENAME"_vieclus_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

    echo -n "$BASENAME,$i,$MAX_MEM"

    LABEL_FILE="${INPUT_FILE%.graph}.labels"

    if [ -f $LABEL_FILE ]; then
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_clustering.txt "$LABEL_FILE")
        EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
        EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
        EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
        EVAL_F1=$(echo "$EVAL_OUT" | awk -F',' '{print $7}')
        EVAL_AC=$(echo "$EVAL_OUT" | awk -F',' '{print $8}')
        EVAL_TP=$(echo "$EVAL_OUT" | awk -F',' '{print $9}')
        EVAL_FP=$(echo "$EVAL_OUT" | awk -F',' '{print $10}')
        EVAL_TN=$(echo "$EVAL_OUT" | awk -F',' '{print $11}')
        EVAL_FN=$(echo "$EVAL_OUT" | awk -F',' '{print $12}')
            
        echo ",$TIME,$EVAL_MOD,$EVAL_N,$EVAL_CC,$EVAL_F1,$EVAL_AC,$EVAL_TP,$EVAL_FP,$EVAL_TN,$EVAL_FN"
    else
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_clustering.txt)
        EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
        EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
        EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
            
        echo ",$TIME,$EVAL_MOD,$EVAL_N,$EVAL_CC"
    fi

    rm -rf "$BASENAME"_vieclus_time_mem.txt
done

rm -rf "$BASENAME"_clustering.txt