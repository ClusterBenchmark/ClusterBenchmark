#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Device: cpu (default) installs the CPU-only TensorFlow wheel; cuda installs
# the bundled-CUDA wheel for GPU runs (Protocol B). Nothing else differs, so we
# switch the wheel here rather than keeping two solver.json files.
DEVICE="${1:-cpu}"
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo "usage: $0 [cpu|cuda]" >&2
    exit 1
fi

mkdir google-research
cp dmon.patch google-research/

cd google-research/
git init
git remote add -f origin https://github.com/google-research/google-research.git
git config core.sparseCheckout true
echo "graph_embedding/dmon/" >> .git/info/sparse-checkout
git checkout 376257a6d0b88a6048a554e25600b123d85b8e86
git read-tree -m -u HEAD

# Compat-only patch (TF2 add_variable -> add_weight); the method is unchanged.
git apply dmon.patch

# Our driver runs from here so it can import graph_embedding.dmon.* directly.
cp ../run_dmon.py .

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# TensorFlow >=2.16 defaults to Keras 3, which breaks the authors' TF2/Keras-2
# code (add_weight signature, sparse Input, model.losses). TF 2.15 has no
# Python 3.12 wheel, so instead of pinning back the interpreter we take Google's
# supported path: a current TF plus the tf-keras (Keras 2) package, selected at
# runtime by TF_USE_LEGACY_KERAS=1 (set in run_dmon.py before TF is imported).
if [[ "$DEVICE" == "cuda" ]]; then
    pip install "tensorflow[and-cuda]==2.17.1"
else
    pip install "tensorflow==2.17.1"
fi

pip install "tf-keras~=2.17.0"
pip install absl-py "numpy<2" scipy scikit-learn

echo "Environment setup complete ($DEVICE)."
