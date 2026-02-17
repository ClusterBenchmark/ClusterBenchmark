#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

git clone https://github.com/pyrobits/DGCluster.git

cp dgcluster.patch DGCluster/

cd DGCluster/

git checkout e5ede94ef796a176a092bad14cc20a5e551333f6

git apply dgcluster.patch

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install python packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install scipy
pip install torch_geometric
pip install scikit-learn

echo "Environment setup complete."