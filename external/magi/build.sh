#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

git clone https://github.com/EdisonLeeeee/MAGI.git

cp magi.patch MAGI/

cd MAGI/

git checkout 6313854c0748d58fee11e84d7e6b73221e9c1557

git apply magi.patch

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install python packages
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
pip install torch-sparse -f https://pytorch-geometric.com/whl/torch-2.8.0+cpu.html
pip install torch_geometric
pip install torch-scatter -f https://pytorch-geometric.com/whl/torch-2.8.0+cpu.html
pip install scikit-learn
pip install munkres
pip install matplotlib

echo "Environment setup complete."