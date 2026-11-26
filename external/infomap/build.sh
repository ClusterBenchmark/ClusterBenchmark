#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# infomap provides the map-equation solver; numpy backs graphio's CSR memmap.
pip install infomap numpy

echo "Environment setup complete."