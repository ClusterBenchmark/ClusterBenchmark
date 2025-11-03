#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <tl> <p>"
    exit 1
fi

INPUT_FILE=$1
K=$2
TL=$3
P=$4
BASENAME=$(basename "$INPUT_FILE" .graph)

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

echo -n "$BASENAME"

for i in $(seq 1 $K);
do
    TIME=$(mpirun -n $P vieclus "$INPUT_FILE" --time_limit="$TL" --seed="$i" --output_filename="$BASENAME"_clustering.txt | grep 'Best solution found after' | awk '{print $5}')

    EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_clustering.txt)
    EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
    EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
    EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')

    echo -n ",$TIME,$EVAL_MOD,$EVAL_N,$EVAL_CC"
done

echo ""
rm -rf "$BASENAME"_clustering.txt