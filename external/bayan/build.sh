#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# bayanpy solves the modularity ILP with Gurobi (gurobipy); numpy backs graphio's
# CSR memmap. Gurobi needs a licence for anything beyond tiny graphs.
pip install gurobipy networkx bayanpy scipy numpy

echo "Environment setup complete."
