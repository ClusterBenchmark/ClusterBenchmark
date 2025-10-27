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

./CONVERT_GRAPH "$INPUT_FILE" "$BASENAME".graph

./streamcom -f "$BASENAME".graph --vmax-start 10000 --vmax-end 10000 -o "$BASENAME" --niter "$K" > "$BASENAME"_hollocou_out.txt

HOLLOCOU_OUT=$(cat "$BASENAME"_hollocou_out.txt | grep "Algorithm time:" | awk '{printf "%.3f,",$3 / 1000}')

echo -n "$BASENAME"

for i in $(seq 1 $K);
do
    FILE="$BASENAME"_$((i - 1))_10000
    ./CONVERT_CLUSTER "$FILE" "$FILE".txt
    if [ -f $FILE ]; then
        TIME=$(echo "$HOLLOCOU_OUT" | awk -F',' -v var="$((i))" '{print $var}')
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE".txt)
        EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
        EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
        EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')

        echo -n ",$TIME,$EVAL_MOD,$EVAL_N,$EVAL_CC"
    else
        echo -n ",tle,tle,tle,tle"
    fi
done

echo ""

rm -rf "$BASENAME"_* "$BASENAME".graph