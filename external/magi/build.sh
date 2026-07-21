#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Device: cpu (default) or cuda for GPU runs (Protocol B). MAGI pins torch 2.8.0
# because torch-sparse / torch-scatter ship as compiled wheels tied to an exact
# torch build; the cuda branch uses the matching CUDA wheels. CUDA_TAG may need
# to match the server's CUDA version (default cu121).
DEVICE="${1:-cpu}"
CUDA_TAG="${2:-cu121}"
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo "usage: $0 [cpu|cuda] [cuda_tag e.g. cu121]" >&2
    exit 1
fi

git clone https://github.com/EdisonLeeeee/MAGI.git
cd MAGI/
git checkout 6313854c0748d58fee11e84d7e6b73221e9c1557

# No patch: the authors' files are used unchanged. Our driver imports the model
# and sampling helpers and runs everything else; see run_magi.py.
cp ../run_magi.py .

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    TAG="cu${CUDA_TAG#cu}"
    pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0
    pip install torch-sparse torch-scatter -f "https://data.pyg.org/whl/torch-2.8.0+${TAG}.html"
else
    pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
    pip install torch-sparse torch-scatter -f "https://data.pyg.org/whl/torch-2.8.0+cpu.html"
fi

# matplotlib is imported at the top of magi/clustering_metric.py (pulled in via
# magi/utils.py), so it is required even though our driver does its own readout.
pip install torch_geometric scikit-learn munkres matplotlib

echo "Environment setup complete ($DEVICE)."
