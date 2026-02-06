#!/usr/bin/env bash
set -e

# Clone repo
git clone https://github.com/KaHIP/CluStRE.git

cp clustre.patch CluStRE/

cd CluStRE

git checkout b95c62bdfc982a3166a550d245a5163fd9c44ed9

git apply clustre.patch

./compile.sh

cp deploy/clustre ../

echo "Environment setup complete."