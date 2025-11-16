#!/usr/bin/env bash
set -e

# Clone repo
git clone https://github.com/VieClus/VieClus.git

cp vieclus.patch VieClus/

cd VieClus

git checkout f40e2805cac4efe2002c6af4a29398f9f0b97bfd

git apply vieclus.patch

./compile_withcmake.sh

cp deploy/vieclus ../

echo "Environment setup complete."