#!/usr/bin/env bash
# Tier 2 -- Scalability & accelerators. Same author-faithful DEFAULTS as Protocol
# A (no tuning); the ONLY things that vary here are thread count and device. It
# isolates the hardware/parallelism/GPU effect: A -> this tier is purely "what
# does more compute buy?". Two sweeps, both writing full JSONL records (no CSV):
#
#   1. CPU full-machine    -- every threads-capable solver at nproc threads on
#      the CPU. Paired with the same solver's 1-thread Protocol A row, this is a
#      two-point "what does the whole box buy?" comparison -- deliberately NOT a
#      scaling curve. Report it as a FULL-MACHINE SPEEDUP, not "scales to N
#      cores" (two points cannot support a scaling-behaviour claim). Speedup
#      means different things per solver and that is the finding: a fixed-epoch
#      ML method gets FASTER (wall time), while an anytime solver at a fixed time
#      budget (vieclus) instead gets BETTER (more MPI islands -> higher
#      modularity / earlier time-to-best at the same wall clock). To recover an
#      actual curve for a specific solver, pass a multi-point THREAD_LIST.
#   2. GPU accelerator     -- every GPU-capable solver on cuda at full threads.
#      Compare against its CPU point from sweep 1 (and its 1-thread A row) for the
#      speedup, and watch for the VRAM ceiling: dense O(n^2) ML can MLE EARLIER on
#      the GPU than on the 120GB host, a genuine "accelerator raises throughput
#      but lowers the memory ceiling" result, not a bug.
#
# Classical single-threaded CPU-only solvers (louvain, leiden, combo, ... bayan)
# have nothing to sweep -- their Protocol A row IS their scalability story -- so
# they are deliberately absent here.
#
# Records land in one JSONL per solver (harness appends), each tagged with its
# `threads` and `device`, so every (solver, instance, threads, device) point is
# distinguishable. Protocol label is S.
#
# Usage:
#   scripts/run_scalability.sh CSR_DIR LABELS_DIR OUT_DIR \
#       [TIME] [MEM_GB] [RUNS] [GRACE] [STARTUP_GRACE]
#
# CPU sweep first (safe anywhere), then it does the GPU sweep automatically if a
# CUDA build is present. Override the thread points, the solver sets, or skip a
# sweep entirely via the env vars documented below, e.g.:
#   THREAD_LIST="1 8 32" scripts/run_scalability.sh /tmp/prep /home/.../gt out_scale
#   GPU_SOLVERS="" scripts/run_scalability.sh ...        # CPU thread study only
#   PAR_SOLVERS="" scripts/run_scalability.sh ...        # GPU study only

set -u

here="$(cd "$(dirname "$0")/.." && pwd)"
[ "$#" -ge 3 ] || { echo "usage: $0 CSR_DIR LABELS_DIR OUT_DIR [TIME MEM RUNS GRACE STARTUP_GRACE]"; exit 1; }
CSR_DIR="$1"; LABELS_DIR="$2"; OUT_DIR="$3"
TIME="${4:-3600}"; MEM="${5:-120}"; RUNS="${6:-5}"
GRACE="${7:-300}"; STARTUP="${8:-600}"
mkdir -p "$OUT_DIR"

NPROC="$(nproc)"

# Thread points. Default is the single full-machine point (nproc): the 1-thread
# baseline already exists as each solver's Protocol A row, so this tier only adds
# the other end of the comparison. Set THREAD_LIST to a multi-point grid (e.g.
# "1 2 4 8 16 32") if you want an actual scaling curve for some solver.
THREAD_LIST="${THREAD_LIST:-$NPROC}"

# Solvers whose solver.json declares threads:true (CPU thread sweep). vieclus is
# the only threads-capable classical (MPI islands); the rest are the ML methods.
PAR_SOLVERS="${PAR_SOLVERS:-vieclus commdgi dgcluster dmon gnns lim magi magi-sage ucode}"
# Solvers whose solver.json declares gpu:true (accelerator sweep) -- all ML.
GPU_SOLVERS="${GPU_SOLVERS:-commdgi dgcluster dmon gnns lim magi magi-sage ucode}"

# Detect a CUDA-capable torch once, so the GPU sweep is skipped cleanly on a
# CPU-only box rather than erroring per run. Override with FORCE_GPU=1.
have_gpu() {
    [ "${FORCE_GPU:-0}" = "1" ] && return 0
    command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1
}

run_one() {  # solver device threads
    local s="$1" dev="$2" thr="$3" G inst
    for G in "$CSR_DIR"/*.csr; do
        [ -e "$G" ] || continue
        inst="$(basename "$G" .csr)"
        local args=(--solver "$s" --graph "$G"
              --runs "$RUNS" --time "$TIME" --memory "$MEM" --threads "$thr"
              --device "$dev" --grace "$GRACE" --startup-grace "$STARTUP"
              --protocol S --out "$OUT_DIR/$s.jsonl")
        [ -f "$LABELS_DIR/$inst.labels" ] && args+=(--labels "$LABELS_DIR/$inst.labels")
        [ -f "$CSR_DIR/$inst.feat" ] && args+=(--features "$CSR_DIR/$inst.feat")
        echo "[$(date +%T)] $s / $inst  dev=$dev threads=$thr"
        python3 "$here/scripts/harness.py" "${args[@]}"
    done
}

echo "nproc=$NPROC thread_list=[$THREAD_LIST] time=${TIME}s mem=${MEM}GB runs=$RUNS"
echo "== CPU full-machine (pairs with the 1-thread Protocol A rows) =="
for s in $PAR_SOLVERS; do
    for thr in $THREAD_LIST; do
        run_one "$s" cpu "$thr"
    done
done

echo "== GPU accelerator =="
if [ -n "$GPU_SOLVERS" ] && have_gpu; then
    for s in $GPU_SOLVERS; do
        run_one "$s" cuda "$NPROC"
    done
else
    echo "  (skipped: no CUDA device detected, or GPU_SOLVERS empty; set FORCE_GPU=1 to force)"
fi

echo "[$(date +%T)] Scalability complete -> $OUT_DIR/*.jsonl"
