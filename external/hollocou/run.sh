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

ulimit -v $(($MEM_LIMIT * 1024 * 1024))

./CONVERT_GRAPH "$INPUT_FILE" "$BASENAME".graph

timeout --kill-after=10s $(($TIMEOUT * $K + 600)) /usr/bin/time -v ./streamcom -f "$BASENAME".graph --vmax-start 10000 --vmax-end 10000 -o "$BASENAME" --niter "$K" > "$BASENAME"_hollocou_out.txt 2> "$BASENAME"_hollocou_time_mem.txt

STATUS=$?

HOLLOCOU_OUT=$(cat "$BASENAME"_hollocou_out.txt | grep "Algorithm time:" | awk '{printf "%.3f,",$3 / 1000}')
MAX_MEM=$(cat "$BASENAME"_hollocou_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

for i in $(seq 1 $K);
do
    echo -n "hollocou,$BASENAME,$i,$MAX_MEM,$STATUS"

    FILE="$BASENAME"_$((i - 1))_10000
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    ./CONVERT_CLUSTER "$FILE" "$FILE".txt
    if [ -f $FILE ]; then
        TIME=$(echo "$HOLLOCOU_OUT" | awk -F',' -v var="$((i))" '{print $var}')

        if [ -f $LABEL_FILE ]; then
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE".txt "$LABEL_FILE")
            echo ",$TIME,""$EVAL_OUT"
        else
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE".txt)
            echo ",$TIME,""$EVAL_OUT"
        fi
    else
        echo ""
    fi
done

rm -rf "$BASENAME"_* "$BASENAME".graph