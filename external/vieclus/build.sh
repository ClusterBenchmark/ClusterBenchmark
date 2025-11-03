#!/usr/bin/env bash
set -e

# Clone repo
git clone https://github.com/VieClus/VieClus.git

cp vieclus.patch VieClus/

cd VieClus

git apply vieclus.patch

./compile_withcmake.sh

cp deploy/vieclus ../

echo "Environment setup complete."