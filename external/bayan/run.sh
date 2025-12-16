#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_graph_file>"
    exit 1
fi

INPUT_FILE=$1
BASENAME=$(basename "$INPUT_FILE" .graph)

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

source .venv/bin/activate

/usr/bin/time -v python3 run_bayan.py --input_file "$INPUT_FILE" --output_file "$BASENAME""_bayan.txt" > "$BASENAME"_bayan_out.txt 2> "$BASENAME"_bayan_time_mem.txt

PYTHON_OUT=$(cat "$BASENAME"_bayan_out.txt)
MAX_MEM=$(cat "$BASENAME"_bayan_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

rm "$BASENAME"_bayan_out.txt

echo -n "$BASENAME,$MAX_MEM"

FILE="$BASENAME"_bayan.txt
LABEL_FILE="${INPUT_FILE%.graph}.labels"
if [ -f $FILE ]; then
    TIME=$(echo "$PYTHON_OUT" | grep 'Elapsed' | awk '{print $2}')
    if [ -f $LABEL_FILE ]; then
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE" "$LABEL_FILE")
        echo ",$TIME,""$EVAL_OUT"
    else
        EVAL_OUT=$(../../EVAL "$INPUT_FILE" "$FILE")
        echo ",$TIME,""$EVAL_OUT"
    fi
else
    echo ""
fi

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_bayan*