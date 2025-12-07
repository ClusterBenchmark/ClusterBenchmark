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

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

for i in $(seq 1 $K);
do
    TIME=$(/usr/bin/time -v mpirun -n $THREADS ./vieclus "$INPUT_FILE" --time_limit="$TIMEOUT" --seed="$i" --output_filename="$BASENAME"_clustering.txt 2> "$BASENAME"_vieclus_time_mem.txt | grep 'Best solution found after' | awk '{print $5}')
    MAX_MEM=$(cat "$BASENAME"_vieclus_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

    echo -n "$BASENAME,$i,$MAX_MEM"

    LABEL_FILE="${INPUT_FILE%.graph}.labels"

    if [ -f $LABEL_FILE ]; then
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_clustering.txt "$LABEL_FILE")
        echo ",$TIME,""$EVAL_OUT"
    else
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_clustering.txt)
        echo ",$TIME,""$EVAL_OUT"
    fi

    rm -rf "$BASENAME"_vieclus_time_mem.txt
done

rm -rf "$BASENAME"_clustering.txt