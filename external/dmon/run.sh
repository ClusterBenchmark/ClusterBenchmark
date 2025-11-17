#!/bin/bash

if [ "$#" -ne 5 ] && [ "$#" -ne 6 ]; then
    echo "Usage: $0 <path_to_graph_file> <k> <timeout_seconds> <threads> <c> [<features>]"
    exit 1
fi

INPUT_FILE=$1
K=$2
TIMEOUT=$3
THREADS=$4
C=$5
FEATURES=${6:-} # Set to empty if not provided

BASENAME=$(basename "$INPUT_FILE" .graph)

# Make sure we are in the script's directory, so we can find the executables.
cd "$(dirname "$0")"

# If the input file path is relative, make it absolute.
if [[ "$INPUT_FILE" != /* ]]; then
    INPUT_FILE="$(pwd)/$INPUT_FILE"
fi

cd google-research/

source .venv/bin/activate

export OMP_NUM_THREADS="$THREADS"

# Construct the python command
PYTHON_CMD="/usr/bin/time -v python3 -m graph_embedding.dmon.train_metis --graph_path=\"$INPUT_FILE\" --n_clusters=\"$C\" --n_runs=\"$K\" --n_epochs=1000 --dropout_rate=0.5 --timeout=\"$TIMEOUT\" --n_threads=\"$THREADS\" --output_path=\"$BASENAME""_dmon_\""

if [ -n "$FEATURES" ]; then
    PYTHON_CMD="$PYTHON_CMD --features_path=\"$FEATURES\""
fi

# Execute the command
eval "$PYTHON_CMD > \"$BASENAME\"_dmon_out.txt 2> \"$BASENAME\"_dmon_time_mem.txt"


# timeout -s SIGTERM 3600s python3 -m graph_embedding.dmon.train_metis --graph_path="$INPUT_FILE" --output_path="$BASENAME""_dmon_" --n_clusters="$C" --n_runs="$K" --n_epochs=1000 --dropout_rate=0.5 2> /dev/null > "$BASENAME"_dmon_out.txt

PYTHON_OUT=$(cat "$BASENAME"_dmon_out.txt)
MAX_MEM=$(cat "$BASENAME"_dmon_time_mem.txt | grep 'Maximum resident set size' | awk '{print $6}')

# PYTHON_OUT=$(cat "$BASENAME"_dmon_out.txt)

rm "$BASENAME"_dmon_out.txt

for i in $(seq 1 $K);
do
    echo -n "$BASENAME,$i,$MAX_MEM"

    FILE="$BASENAME"_dmon_$((i - 1)).txt
    LABEL_FILE="${INPUT_FILE%.graph}.labels"
    if [ -f $FILE ]; then
        TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 3 - 2))" '{print $var}')
        IT=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 3 - 1))" '{print $var}')
        MOD=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 3))" '{print $var}')

        if [ -f $LABEL_FILE ]; then
            EVAL_OUT=$(../../../EVAL "$INPUT_FILE" "$FILE" "$LABEL_FILE")
            EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
            EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
            EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
            EVAL_F1=$(echo "$EVAL_OUT" | awk -F',' '{print $7}')
            EVAL_AC=$(echo "$EVAL_OUT" | awk -F',' '{print $8}')
            EVAL_TP=$(echo "$EVAL_OUT" | awk -F',' '{print $9}')
            EVAL_FP=$(echo "$EVAL_OUT" | awk -F',' '{print $10}')
            EVAL_TN=$(echo "$EVAL_OUT" | awk -F',' '{print $11}')
            EVAL_FN=$(echo "$EVAL_OUT" | awk -F',' '{print $12}')
            
            echo ",$TIME,$IT,$MOD,$EVAL_MOD,$EVAL_N,$EVAL_CC,$EVAL_F1,$EVAL_AC,$EVAL_TP,$EVAL_FP,$EVAL_TN,$EVAL_FN"
        else
            EVAL_OUT=$(../../../EVAL "$INPUT_FILE" "$FILE")
            EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
            EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
            EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')
            
            echo ",$TIME,$IT,$MOD,$EVAL_MOD,$EVAL_N,$EVAL_CC"
        fi
    else
        if [ -f $LABEL_FILE ]; then
            echo ",tle,tle,tle,tle,tle,tle,tle,tle,tle,tle,tle,tle"
        else
            echo ",tle,tle,tle,tle,tle,tle"
        fi
    fi
    
    # FILE="$BASENAME"_dmon_$((i - 1)).txt
    # if [ -f $FILE ]; then
    #     TIME=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2 - 1))" '{print $var}')
    #     MOD=$(echo "$PYTHON_OUT" | awk -F',' -v var="$((i * 2))" '{print $var}')
    #     EVAL_OUT=$(../../../EVAL "$INPUT_FILE" "$FILE")
    #     EVAL_MOD=$(echo "$EVAL_OUT" | awk -F',' '{print $4}')
    #     EVAL_N=$(echo "$EVAL_OUT" | awk -F',' '{print $5}')
    #     EVAL_CC=$(echo "$EVAL_OUT" | awk -F',' '{print $6}')

    #     echo -n ",$TIME,$MOD,$EVAL_MOD,$EVAL_N,$EVAL_CC"
    # else
    #     echo -n ",tle,tle,tle,tle"
    # fi
done

# echo "5. Cleaning up..."
rm -rf "$BASENAME"_dmon_*.txt