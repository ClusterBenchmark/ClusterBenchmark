#!/usr/bin/env bash
# Protocol A (out-of-the-box) for every migrated solver over a set of prepared
# instances. Each solver runs with its author-faithful defaults. Real features
# are attached when a <name>.feat sits next to the CSR (attributed graphs);
# solvers that do not consume features or a target k simply do not receive them.
# One JSONL of full records per solver is written to OUT_DIR (no CSV reduction).
#
# Solvers run sequentially, so each gets the full --memory budget. A per-run
# watchdog in the harness hard-kills any run that exceeds --time + grace, so a
# solver that ignores its own limit (or MLEs) is bounded, not left to run away.
#
# Usage:
#   scripts/run_protocol_a.sh CSR_DIR LABELS_DIR OUT_DIR \
#       [DEVICE] [TIME] [MEM_GB] [RUNS] [THREADS] [GRACE] [STARTUP_GRACE]
#
# CPU smoke first (recommended), then the real GPU run:
#   scripts/run_protocol_a.sh /tmp/prep /home/.../ground-truth out_cpu  cpu  3600 120 5 $(nproc) 300 600
#   scripts/run_protocol_a.sh /tmp/prep /home/.../ground-truth out_cuda cuda 3600 120 5 $(nproc) 300 600
#
# DEVICE is passed to every solver; classical solvers (gpu:false) ignore cuda and
# run on the CPU regardless, so one run covers the whole set.

set -u

here="$(cd "$(dirname "$0")/.." && pwd)"
[ "$#" -ge 3 ] || { echo "usage: $0 CSR_DIR LABELS_DIR OUT_DIR [DEVICE TIME MEM RUNS THREADS GRACE STARTUP_GRACE]"; exit 1; }
CSR_DIR="$1"; LABELS_DIR="$2"; OUT_DIR="$3"
DEVICE="${4:-cpu}"; TIME="${5:-3600}"; MEM="${6:-120}"; RUNS="${7:-5}"
THREADS="${8:-$(nproc)}"; GRACE="${9:-300}"; STARTUP="${10:-600}"
mkdir -p "$OUT_DIR"

# clustre-strong is intentionally excluded (dropped from the run set: it trails
# plain VieClus and its anytime wall time is hard to present). Override the list
# with the SOLVERS env var to run a subset, e.g. SOLVERS="leiden vieclus" ...
SOLVERS="${SOLVERS:-louvain cnm walktrap combo infomap leiden bayan hollocou clustre-fast vieclus dmon commdgi gnns ucode dgcluster magi magi-sage lim}"

echo "device=$DEVICE time=${TIME}s mem=${MEM}GB runs=$RUNS threads=$THREADS grace=$GRACE startup=$STARTUP"
for s in $SOLVERS; do
    for G in "$CSR_DIR"/*.csr; do
        [ -e "$G" ] || continue
        inst="$(basename "$G" .csr)"
        args=(--solver "$s" --graph "$G"
              --runs "$RUNS" --time "$TIME" --memory "$MEM" --threads "$THREADS"
              --device "$DEVICE" --grace "$GRACE" --startup-grace "$STARTUP"
              --protocol A --out "$OUT_DIR/$s.jsonl")
        [ -f "$LABELS_DIR/$inst.labels" ] && args+=(--labels "$LABELS_DIR/$inst.labels")
        [ -f "$CSR_DIR/$inst.feat" ] && args+=(--features "$CSR_DIR/$inst.feat")
        echo "[$(date +%T)] $s / $inst"
        python3 "$here/scripts/harness.py" "${args[@]}"
    done
done
echo "[$(date +%T)] Protocol A complete -> $OUT_DIR/*.jsonl"
