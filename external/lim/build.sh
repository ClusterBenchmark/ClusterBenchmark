#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Device: cpu (default) installs the CPU-only PyTorch wheel; cuda installs the
# default CUDA-enabled wheel for GPU runs (Protocol B). Nothing else differs, so
# we switch the wheel here rather than keeping two solver.json files.
DEVICE="${1:-cpu}"
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo "usage: $0 [cpu|cuda]" >&2
    exit 1
fi

git clone https://github.com/wuanghoong/Less-is-More.git
cd Less-is-More/
git checkout c2275f083bc5ecc4e6681303c610c22a53c0f499

# Compat-only patch: a single device-correctness fix in DGI.forward so the model
# runs on GPU. The method is unchanged; main.py is left pristine and unused.
git apply ../lim.patch

# Our driver runs from here so it can import model.py / DGI.py.
cp ../run_lim.py .

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    # cu124: newest CUDA build the lab GPU driver (max CUDA 12.6) can initialise;
    # the default index ships a cu128 wheel that a 12.6 driver rejects as too old.
    # (torch 2.8.0 is not published for cu124, so it is unpinned here.)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
else
    pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
fi

pip install torch_geometric scikit-learn networkx

echo "Environment setup complete ($DEVICE)."
