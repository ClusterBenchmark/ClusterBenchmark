#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

mkdir google-research
cp dmon.patch google-research/

cd google-research/
git init
git remote add -f origin https://github.com/google-research/google-research.git
git config core.sparseCheckout true
echo "graph_embedding/dmon/" >> .git/info/sparse-checkout
git checkout 376257a6d0b88a6048a554e25600b123d85b8e86
git read-tree -m -u HEAD

git apply dmon.patch
cp ../train_metis.py graph_embedding/dmon/

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install python packages
pip install absl-py
pip install numpy
pip install scipy
pip install tensorflow
pip install -U scikit-learn

echo "Environment setup complete."