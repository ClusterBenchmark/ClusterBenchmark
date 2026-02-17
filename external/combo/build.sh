#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install python-igraph (C core + Python bindings)
pip install igraph
pip install cdlib
pip install pycombo

echo "Environment setup complete."