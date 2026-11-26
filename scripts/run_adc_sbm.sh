#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
PYBIN="$here/scripts/.venv/bin/python"

if [ ! -x "$PYBIN" ]; then
    PYBIN="python3"
fi

exec "$PYBIN" "$here/scripts/run_adc_sbm_sweep.py" "$@"
