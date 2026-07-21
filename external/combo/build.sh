#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# pycombo runs the Combo algorithm on a networkx graph; numpy backs graphio's
# CSR memmap. The old cdlib/igraph wrapper is no longer used.
pip install pycombo networkx numpy

echo "Environment setup complete."
