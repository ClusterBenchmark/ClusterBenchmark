#!/usr/bin/env bash
set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

pip install infomap

echo "Environment setup complete."