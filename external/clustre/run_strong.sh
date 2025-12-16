#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds>"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
BASENAME=$(basename "$INPUT_FILE" .graph)

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

for i in $(seq 1 $K);
do
    /usr/bin/time -v ./clustre "$INPUT_FILE" --seed="$i" --one_pass_algorithm=modularity --mode=strong --ext_clustering_algorithm=VieClus --ext_algorithm_time="$TIMEOUT" > "$BASENAME"_clustre_out.txt 2> "$BASENAME"_clustre_time_mem.txt
    MAX_MEM=$(cat "$BASENAME"_clustre_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

    T1=$(cat "$BASENAME"_clustre_out.txt | grep 'Mapping Time' | awk '{print $3}')
    T2=$(cat "$BASENAME"_clustre_out.txt | grep 'New best' | tail -n 1 | awk '{print $6}')
    TIME=$(echo "$T1 + $T2" | bc)

    echo -n "$BASENAME,$i,$MAX_MEM"

    LABEL_FILE="${INPUT_FILE%.graph}.labels"

    if [ -f $LABEL_FILE ]; then
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_strong.txt "$LABEL_FILE")
        echo ",$TIME,""$EVAL_OUT"
    else
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$BASENAME"_strong.txt)
        echo ",$TIME,""$EVAL_OUT"
    fi

    rm -rf "$BASENAME"_clustre_time_mem.txt
done

rm -rf "$BASENAME"_*