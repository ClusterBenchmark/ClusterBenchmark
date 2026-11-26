#!/usr/bin/env bash
# clustre-fast and clustre-strong share one binary + driver, built once under
# external/clustre. Delegate there; that build is idempotent.
exec "$(dirname "$0")/../clustre/build.sh"
