#!/usr/bin/env bash

# Shared build for both CluStRE operating points (clustre-fast, clustre-strong).
# They invoke the same binary and driver with a different --mode, so this builds
# once; the thin clustre-fast/ and clustre-strong/ build scripts delegate here,
# and this is idempotent so building either variant compiles the stack only once.
#
# System prerequisites: an MPI implementation (KaHIP/VieClus/KaGen link against
# it) and CMake + a C++14 compiler. On Debian/Ubuntu:
#     sudo apt install libopenmpi-dev cmake g++
# Argtable is vendored in the repo, so it needs no system package.

cd "$(dirname "$0")"

set -e

# venv for the driver: numpy converts our binary CSR to CluStRE's ParHIP format.
if [ ! -d .venv ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install numpy
else
    source .venv/bin/activate
fi

if [ ! -x clustre ]; then
    if [ ! -d CluStRE ]; then
        git clone https://github.com/KaHIP/CluStRE.git
    fi
    cp clustre.patch CluStRE/
    cd CluStRE
    git checkout b95c62bdfc982a3166a550d245a5163fd9c44ed9
    # Apply the compat patch only if it is not already applied, so a rebuild
    # after a failed compile (e.g. a missing system dep) does not error out.
    if ! git apply --reverse --check clustre.patch 2>/dev/null; then
        git apply clustre.patch
    fi
    rm -rf build   # drop any cache from a previous failed configure
    ./compile.sh
    cp deploy/clustre ../
    cd ..
fi

echo "Environment setup complete."
