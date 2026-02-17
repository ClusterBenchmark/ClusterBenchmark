#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

git clone https://github.com/wuanghoong/Less-is-More.git

cp lim.patch Less-is-More/

cd Less-is-More/

git checkout c2275f083bc5ecc4e6681303c610c22a53c0f499

git apply lim.patch

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install python packages
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
pip install torch_geometric
pip install scikit-learn
pip install matplotlib

echo "Environment setup complete."