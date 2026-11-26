#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

# System prerequisites: an MPI implementation (VieClus parallelises the memetic
# search across MPI ranks) and CMake + a C++14 compiler. On Debian/Ubuntu:
#     sudo apt install libopenmpi-dev cmake g++
# KaHIP and Argtable are vendored in the repo, so they need no system package.

git clone https://github.com/KaHIP/VieClus.git

cd VieClus

git checkout 0e27f24387ab1dcfeaf6d75cd0bc680531207c27

# One compat patch: teach KaHIP's graph reader to consume our binary CSR format
# directly, so the harness feeds VieClus the CSR without a METIS text conversion.
git apply ../vieclus.patch

# Build with MPI (default). deploy/vieclus is the CLI binary.
./compile_withcmake.sh

cp deploy/vieclus ../

echo "Environment setup complete."
