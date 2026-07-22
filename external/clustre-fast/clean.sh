#!/usr/bin/env bash
# The build is shared with the sibling variant; clean it via the shared dir so
# one variant's clean does not pull the binary out from under the other.
echo "clustre-fast and clustre-strong share a build; run external/clustre/clean.sh"
