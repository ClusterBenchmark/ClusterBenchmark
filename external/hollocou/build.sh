#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

git clone https://github.com/ahollocou/graph-streaming.git

cd graph-streaming/

git checkout dcdedd162e56852fbef84be01b5d51ef2d7258d8

# One compat patch: add two missing includes (ctime, cstdint) and teach the
# graph reader to consume our binary CSR format directly, so the harness never
# converts the graph to an edge-list file on disk. Everything else is upstream.
git apply ../hollocou.patch

cd cpp/
mkdir -p build
cd build
cmake ..
make

mv streamcom ../../../

echo "Environment setup complete."
