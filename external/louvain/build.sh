#!/usr/bin/env bash
set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install python-igraph (C core + Python bindings).
# numpy is required by scripts/graphio.py for the binary CSR reader.
pip install igraph numpy

echo "Environment setup complete."