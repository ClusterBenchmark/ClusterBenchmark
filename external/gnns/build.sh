#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install python packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install scipy

echo "Environment setup complete."