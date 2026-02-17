#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

git clone https://github.com/FDUDSDE/CommDGI.git

# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install python packages
pip install igraph
pip install torch_geometric
pip install -U scikit-learn
pip install matplotlib

sed -i 's/g = nx.from_numpy_matrix(shifted_mat)/g = nx.from_numpy_array(shifted_mat)/g' CommDGI/evaluation.py
sed -i "s/clf = LogisticRegression(solver=solver, multi_class=multi_class, \*args,/clf = LogisticRegression(solver=solver, \*args,/" CommDGI/DGI.py

cp run_commdgi.py CommDGI/

echo "Environment setup complete."