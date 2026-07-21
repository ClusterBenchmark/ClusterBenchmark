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

git clone https://github.com/AU-DIS/UCODE.git
cd UCODE
git checkout 09f968b2828c684659c420ff60908af46cba20ce

# Compat/perf-only patch (networkx to_scipy_sparse_array, vectorised get_B,
# div-by-zero guards) to utils.py; main.py is left pristine and unused.
git apply ../ucode.patch

# Our driver runs from here so it can import UCODEncoder / Lossfunction / utils.
cp ../run_ucode.py .

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    pip install torch torchvision
else
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
fi

# community (python-louvain) and tqdm are imported at the top of utils.py.
pip install scipy scikit-learn networkx tqdm community

echo "Environment setup complete ($DEVICE)."
