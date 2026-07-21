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

git clone https://github.com/pyrobits/DGCluster.git
cd DGCluster/
git checkout e5ede94ef796a176a092bad14cc20a5e551333f6

# No patch: main.py and utils.py are used unchanged. Our driver imports the GNN
# and loss_fn and runs everything else; see run_dgcluster.py.
cp ../run_dgcluster.py .

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    pip install torch torchvision
else
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
fi

pip install torch_geometric scipy scikit-learn networkx

echo "Environment setup complete ($DEVICE)."
