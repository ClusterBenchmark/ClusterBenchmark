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

git clone https://github.com/FDUDSDE/CommDGI.git
git -C CommDGI checkout b61fa2da6413da9b95aad4d717b5da89f6e982e3

# Compat-only patch (networkx from_numpy_matrix, sklearn multi_class); the
# method is unchanged. Neither hunk is on our driver's path, but keeping the
# authors' files runnable preserves provenance.
git -C CommDGI apply ../commdgi.patch

# Our driver runs from here so it can import the authors' model.py / DGI.py.
cp run_commdgi.py CommDGI/

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    pip install torch torchvision
else
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
fi

pip install torch_geometric igraph scikit-learn

echo "Environment setup complete ($DEVICE)."
