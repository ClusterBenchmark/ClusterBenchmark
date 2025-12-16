#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path_to_graph_file> <k>"
    exit 1
fi

INPUT_FILE=$1
K=$2
BASENAME=$(basename "$INPUT_FILE" .graph)

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

for i in $(seq 1 $K);
do
    TIME=$(/usr/bin/time -v ./clustre "$INPUT_FILE" --seed="$i" --one_pass_algorithm=modularity --mode=light 2> "$BASENAME"_clustre_time_mem.txt | grep 'Total Time:' | awk '{print $3}')
    MAX_MEM=$(cat "$BASENAME"_clustre_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

    echo -n "$BASENAME,$i,$MAX_MEM"

    LABEL_FILE="${INPUT_FILE%.graph}.labels"

    if [ -f $LABEL_FILE ]; then
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_light.txt "$LABEL_FILE")
        echo ",$TIME,""$EVAL_OUT"
    else
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_light.txt)
        echo ",$TIME,""$EVAL_OUT"
    fi

    rm -rf "$BASENAME"_clustre_time_mem.txt
done

rm -rf "$BASENAME"_*