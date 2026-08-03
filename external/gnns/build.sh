#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Device: cpu (default) installs the CPU-only PyTorch wheel; cuda installs the
# default CUDA-enabled wheel for GPU runs (Protocol B). GNNS's Engine picks up
# the GPU automatically when torch.cuda is available, so the wheel is the switch.
DEVICE="${1:-cpu}"
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo "usage: $0 [cpu|cuda]" >&2
    exit 1
fi

# gnns.py (the authors' algorithm) and run_gnns.py are vendored in this repo,
# so there is nothing to clone; see gnns.py's header for the notebook provenance.

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    # cu124: newest CUDA build the lab GPU driver (max CUDA 12.6) can initialise;
    # the default index ships a cu128 wheel that a 12.6 driver rejects as too old.
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
else
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
fi

pip install scipy networkx

echo "Environment setup complete ($DEVICE)."
