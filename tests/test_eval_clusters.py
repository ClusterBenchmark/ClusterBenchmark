#!/usr/bin/env python3
"""
Lightweight verification for scripts/eval_clusters.py

The tests compare ARI/NMI/purity outputs against those from the C-based EVAL tool
and ensure that permuting cluster identifiers leaves the Python metrics unchanged.

If scikit-learn (and its numpy dependency) is not available, the tests are skipped.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_BIN = ROOT / "EVAL"
PY_EVAL = ROOT / "scripts" / "eval_clusters.py"
DATA_DIR = ROOT / "tests" / "data"

PRED_PERFECT = DATA_DIR / "bridge_pred_perfect.labels"
PRED_PERFECT_RENAMED = DATA_DIR / "bridge_pred_perfect_renamed.labels"
TRUTH = DATA_DIR / "bridge_truth.labels"
GRAPH = DATA_DIR / "bridge.graph"


def dependencies_available() -> bool:
    try:
        import sklearn  # type: ignore  # noqa: F401
        import numpy  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


def run_c_eval(pred: Path, truth: Path) -> dict[str, float]:
    result = subprocess.run(
        [str(EVAL_BIN), str(GRAPH), str(pred), str(truth)],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    line = result.stdout.strip().split(",")
    if len(line) < 18:
        raise RuntimeError(f"Unexpected EVAL output: {result.stdout}")
    return {
        "ari": float(line[14]),
        "nmi": float(line[15]),
        "purity": float(line[16]),
        "inverse_purity": float(line[17]),
    }


def run_python_eval(pred: Path, truth: Path) -> dict[str, float]:
    result = subprocess.run(
        ["python3", str(PY_EVAL), "--pred", str(pred), "--truth", str(truth), "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    data = json.loads(result.stdout)
    return data["metrics"]


def approx_equal(a: float, b: float, eps: float = 1e-9) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    return abs(a - b) <= eps


def compare_against_c():
    c_metrics = run_c_eval(PRED_PERFECT, TRUTH)
    py_metrics = run_python_eval(PRED_PERFECT, TRUTH)

    mapping = {
        "ari": "adjusted_rand_index",
        "nmi": "normalized_mutual_information",
        "purity": "purity",
        "inverse_purity": "inverse_purity",
    }
    for c_key, py_key in mapping.items():
        if not approx_equal(c_metrics[c_key], py_metrics[py_key]):
            raise AssertionError(f"{c_key} mismatch: C={c_metrics[c_key]} vs Python={py_metrics[py_key]}")


def verify_label_permutation_invariance():
    base_metrics = run_python_eval(PRED_PERFECT, TRUTH)
    renamed_metrics = run_python_eval(PRED_PERFECT_RENAMED, TRUTH)
    for key in ("adjusted_rand_index", "normalized_mutual_information", "purity", "inverse_purity"):
        if not approx_equal(base_metrics[key], renamed_metrics[key]):
            raise AssertionError(f"{key} changed after relabeling clusters.")


def main() -> int:
    if not dependencies_available():
        print("SKIP python eval tests (scikit-learn / numpy not installed)", file=sys.stderr)
        return 0

    compare_against_c()
    verify_label_permutation_invariance()
    print("Python evaluation tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
