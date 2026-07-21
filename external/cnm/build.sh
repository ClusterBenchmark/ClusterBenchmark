#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# python-igraph provides community_fastgreedy (CNM); numpy backs graphio's CSR
# memory-mapping. The old cdlib/networkx path is no longer used.
pip install igraph numpy

echo "Environment setup complete."
