#!/usr/bin/env bash
# Protocol B (Per-Instance Parameter Tuning) for all tunable solvers across a
# set of target instances (e.g. cora, citeseer, pubmed).
#
# Non-tunable solvers (clustre-fast, cnm, infomap, vieclus) are skipped automatically.
# Learning solvers run on CUDA (if available), classical solvers run on CPU.
#
# Output:
#   Writes params/<solver>.<instance>.json overlays and companion .meta.json provenance.
#
# Usage:
#   scripts/run_protocol_b_tuning.sh CSR_DIR [PARAMS_OUT_DIR] [TRIALS] [TARGET_INSTANCES]

set -e

here="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$here/scripts/.venv/bin/python}"
[ -f "$PYTHON" ] || PYTHON="python3"

CSR_DIR="${1:-/tmp/prep}"
PARAMS_DIR="${2:-params}"
TRIALS="${3:-50}"
INSTANCES="${4:-cora citeseer pubmed}"

# GPU-capable learning solvers tune on CUDA (if device available); classical solvers on CPU.
GPU_SOLVERS="commdgi dgcluster dmon gnns lim magi magi-sage ucode"
CPU_SOLVERS="bayan clustre-strong combo hollocou leiden louvain walktrap"
ALL_TUNABLE="$GPU_SOLVERS $CPU_SOLVERS"

SOLVERS="${SOLVERS:-$ALL_TUNABLE}"

have_gpu() {
    [ "${FORCE_GPU:-0}" = "1" ] && return 0
    command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1
}

mkdir -p "$PARAMS_DIR"

echo "=================================================================="
echo "Protocol B Parameter Tuning"
echo "  CSR_DIR:    $CSR_DIR"
echo "  PARAMS_DIR: $PARAMS_DIR"
echo "  TRIALS:     $TRIALS"
echo "  INSTANCES:  $INSTANCES"
echo "  PYTHON:     $PYTHON"
echo "=================================================================="

for inst in $INSTANCES; do
    graph="$CSR_DIR/$inst.csr"
    if [ ! -f "$graph" ]; then
        echo "[WARNING] Graph $graph not found, skipping $inst"
        continue
    fi

    for s in $SOLVERS; do
        dev="cpu"
        if echo "$GPU_SOLVERS" | grep -qw "$s"; then
            if have_gpu; then
                dev="cuda"
            fi
        fi

        out_json="$PARAMS_DIR/$s.$inst.json"
        echo "[$(date +%T)] Tuning $s on $inst (device=$dev, trials=$TRIALS) -> $out_json"
        
        $PYTHON "$here/scripts/tune.py" \
            --solver "$s" \
            --graphs "$graph" \
            --features-suffix .feat \
            --metric modularity \
            --trials "$TRIALS" \
            --time "${TIME:-3600}" \
            --memory "${MEM:-120}" \
            --threads "${THREADS:-16}" \
            --device "$dev" \
            --out "$out_json"
    done
done

echo "[$(date +%T)] Protocol B tuning complete -> $PARAMS_DIR/"
