#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Device: cpu (default) or cuda for GPU runs. Same pinned torch (2.5.0 -- newest
# release PyG ships prebuilt torch-sparse / torch-scatter wheels for; 2.8.0 has
# none) and the same install strategy as the GCN variant (external/magi). CUDA_TAG
# must be a tag PyG builds for (cu121 or cu124; default cu121).
DEVICE="${1:-cpu}"
CUDA_TAG="${2:-cu121}"
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo "usage: $0 [cpu|cuda] [cuda_tag e.g. cu121]" >&2
    exit 1
fi

git clone https://github.com/EdisonLeeeee/MAGI.git
cd MAGI/
git checkout 6313854c0748d58fee11e84d7e6b73221e9c1557

# No patch: the authors' files are used unchanged. Our driver runs the minibatch
# SAGE variant; see run_magi_sage.py.
cp ../run_magi_sage.py .

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

if [[ "$DEVICE" == "cuda" ]]; then
    TAG="cu${CUDA_TAG#cu}"
    pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
        --index-url "https://download.pytorch.org/whl/${TAG}"
    pip install torch-sparse torch-scatter --only-binary=torch-sparse,torch-scatter \
        -f "https://data.pyg.org/whl/torch-2.5.0+${TAG}.html"
else
    pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 \
        --index-url https://download.pytorch.org/whl/cpu
    pip install torch-sparse torch-scatter --only-binary=torch-sparse,torch-scatter \
        -f "https://data.pyg.org/whl/torch-2.5.0+cpu.html"
fi

# matplotlib is imported at the top of magi/clustering_metric.py (via magi/utils).
pip install torch_geometric scikit-learn munkres matplotlib

# Fail loudly here if the compiled deps did not land (see external/magi/build.sh).
python -c "import torch, torch_geometric, torch_sparse; print('env OK: torch', torch.__version__, '| pyg', torch_geometric.__version__, '| cuda', torch.cuda.is_available())"

echo "Environment setup complete ($DEVICE)."
