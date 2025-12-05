#!/usr/bin/env bash
set -e

git clone https://github.com/ahollocou/graph-streaming.git

cd graph-streaming/

git checkout dcdedd162e56852fbef84be01b5d51ef2d7258d8

cd cpp/

# Adding missing includes
sed -i '11i\#include <ctime>' source/streamcom/main.cpp
sed -i '11i\#include <cstdint>' include/utils.h

mkdir build
cd build
cmake ..
make

mv streamcom ../../../

cd ../../../

gcc -std=gnu17 -O3 -march=native -fopenmp -I ../../include ../../src/graph.c convert_graph.c -o CONVERT_GRAPH

g++ -std=c++17 -O3 -march=native convert_clustering.cpp -o CONVERT_CLUSTER

echo "Environment setup complete."