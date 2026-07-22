#!/usr/bin/env bash
# Convert read-only METIS .graph instances (and sibling .features, if present)
# into the binary CSR / feature formats the harness reads, writing to a WRITABLE
# output directory. Use this when the dataset lives on read-only storage.
#
# Labels are read directly by the harness from their original location, so they
# are NOT copied here -- point run_protocol_a.sh at the original labels dir.
#
# Usage:
#   scripts/prep_instances.sh <out_dir> <graph1.graph> [graph2.graph ...]
#
# Needs scripts/.venv with numpy for the feature converter:
#   python3 -m venv scripts/.venv && scripts/.venv/bin/pip install numpy optuna

set -eu

here="$(cd "$(dirname "$0")/.." && pwd)"
[ "$#" -ge 2 ] || { echo "usage: $0 <out_dir> <graph.graph> [...]"; exit 1; }
OUT="$1"; shift
mkdir -p "$OUT"

PYBIN="$here/scripts/.venv/bin/python"
[ -x "$PYBIN" ] || { echo "missing $PYBIN (numpy venv); see header for setup"; exit 1; }
[ -x "$here/CONVERT" ] || { echo "missing $here/CONVERT; run 'make' first"; exit 1; }

for g in "$@"; do
    name="$(basename "$g" .graph)"
    dir="$(dirname "$g")"
    echo "[$(date +%T)] $name: graph -> CSR"
    "$here/CONVERT" "$g" "$OUT/$name.csr"
    if [ -f "$dir/$name.features" ]; then
        echo "[$(date +%T)] $name: features -> binary"
        "$PYBIN" "$here/scripts/convert_features.py" "$dir/$name.features" --out "$OUT/$name.feat"
    else
        echo "[$(date +%T)] $name: no .features (solvers will use LDP+RNI)"
    fi
done
echo "[$(date +%T)] done. CSR/feat in $OUT"
