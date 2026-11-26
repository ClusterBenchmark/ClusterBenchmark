#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Device: cpu (default) or cuda for GPU runs. torch is pinned to 2.5.0 because
# that is the newest release for which PyG publishes prebuilt torch-sparse /
# torch-scatter wheels -- 2.8.0 has none, so pip falls back to the PyPI sdist and
# fails to compile it (no torch in the build env, no nvcc). The cuda branch pulls
# torch+CUDA from the matching pytorch index so its ABI lines up with the
# +ptXXcuYYY pyg wheels. CUDA_TAG must be a tag PyG builds for (cu121 or cu124;
# default cu121).
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

# matplotlib is imported at the top of magi/clustering_metric.py (pulled in via
# magi/utils.py), so it is required even though our driver does its own readout.
pip install torch_geometric scikit-learn munkres matplotlib

# Fail loudly here if the compiled deps did not land. A mid-script pip failure
# (e.g. the pyg wheel step) under `set -e` otherwise leaves a half-built venv
# with torch present but torch_sparse/torch_geometric missing -- which surfaces
# only later as a per-run ModuleNotFoundError in the harness logs.
python -c "import torch, torch_geometric, torch_sparse; print('env OK: torch', torch.__version__, '| pyg', torch_geometric.__version__, '| cuda', torch.cuda.is_available())"

echo "Environment setup complete ($DEVICE)."
