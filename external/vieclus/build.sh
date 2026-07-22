#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# VieClus ships an official CSR Python interface (KaHIP/VieClus), so no C++/MPI
# build is needed here -- the pinned wheel is the whole solver. numpy backs
# graphio's CSR memmap. The wheel is single-process (no MPI island parallelism).
pip install vieclus==1.3.1 numpy

echo "Environment setup complete."
