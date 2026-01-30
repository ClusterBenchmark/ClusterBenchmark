#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
eval_bin="${root_dir}/EVAL"

if [[ ! -x "${eval_bin}" ]]; then
    echo "EVAL binary not found; run 'make EVAL' first." >&2
    exit 1
fi

run_case() {
    local name="$1"
    local graph="$2"
    local clustering="$3"
    local truth="$4"

    local output
    if [[ -n "${truth}" ]]; then
        output="$("${eval_bin}" "${graph}" "${clustering}" "${truth}")"
    else
        output="$("${eval_bin}" "${graph}" "${clustering}")"
    fi

    local expected_file="${root_dir}/tests/expected/${name}.txt"
    if [[ ! -f "${expected_file}" ]]; then
        echo "Missing expected output for ${name}: ${expected_file}" >&2
        exit 1
    fi

    if ! diff -u "${expected_file}" <(printf "%s\n" "${output}") >/dev/null; then
        echo "Test '${name}' failed." >&2
        printf "Got     : %s\n" "${output}"
        printf "Expected: %s\n" "$(cat "${expected_file}")"
        exit 1
    fi
}

run_case bridge_perfect \
    "${root_dir}/tests/data/bridge.graph" \
    "${root_dir}/tests/data/bridge_pred_perfect.labels" \
    "${root_dir}/tests/data/bridge_truth.labels"

run_case bridge_mismatch \
    "${root_dir}/tests/data/bridge.graph" \
    "${root_dir}/tests/data/bridge_pred_mismatch.labels" \
    "${root_dir}/tests/data/bridge_truth.labels"

echo "All eval tests passed."
