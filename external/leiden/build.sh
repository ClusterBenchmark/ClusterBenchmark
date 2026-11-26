#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# python-igraph provides community_leiden; numpy backs graphio's CSR memmap.
pip install igraph numpy

echo "Environment setup complete."