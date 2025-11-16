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

/usr/bin/time -v ./streamcom -f "$BASENAME".graph --vmax-start 10000 --vmax-end 10000 -o "$BASENAME" --niter "$K" > "$BASENAME"_hollocou_out.txt 2> "$BASENAME"_hollocou_time_mem.txt

HOLLOCOU_OUT=$(cat "$BASENAME"_hollocou_out.txt | grep "Algorithm time:" | awk '{printf "%.3f,",$3 / 1000}')
MAX_MEM=$(cat "$BASENAME"_hollocou_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

for i in $(seq 1 $K);
do
    echo -n "$BASENAME,$i,$MAX_MEM"

    FILE="$BASENAME"_$((i - 1))_10000
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    ./CONVERT_CLUSTER "$FILE" "$FILE".txt
    if [ -f $FILE ]; then
        TIME=$(echo "$HOLLOCOU_OUT" | awk -F',' -v var="$((i))" '{print $var}')

        if [ -f $LABEL_FILE ]; then
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE".txt "$LABEL_FILE")
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
            EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE".txt)
            EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
            EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
            EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
            
            echo ",$TIME,$EVAL_MOD,$EVAL_N,$EVAL_CC"
        fi
    else
        if [ -f $LABEL_FILE ]; then
            echo ",tle,tle,tle,tle,tle,tle,tle,tle,tle,tle"
        else
            echo ",tle,tle,tle,tle"
        fi
    fi
done

rm -rf "$BASENAME"_* "$BASENAME".graph