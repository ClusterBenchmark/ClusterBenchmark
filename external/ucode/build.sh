#!/usr/bin/env bash
set -e

git clone https://github.com/AU-DIS/UCODE.git

cp ucode.patch UCODE/

cd UCODE

git checkout 09f968b2828c684659c420ff60908af46cba20ce

git apply ucode.patch

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install python packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install scipy
pip install scikit-learn
pip install community
pip install tqdm

echo "Environment setup complete."