#!/usr/bin/env python3
"""
Compare clustering assignments using standard community-quality metrics.

Input format (both truth and prediction files):
    - Line i (0-indexed) corresponds to node i.
    - Tokens on each line are the cluster IDs assigned to that node.
    - Prediction files must contain exactly one cluster ID per line.
    - Use --truth-multi when the ground truth may list zero, one, or many IDs per node.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from typing import Dict, List, Sequence

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency check
    np = None

try:
    from sklearn import metrics as sk_metrics
except ImportError:  # pragma: no cover - optional dependency check
    sk_metrics = None

try:
    import igraph as ig
except ImportError:  # pragma: no cover - optional dependency check
    ig = None

try:
    from cdlib import evaluation as cd_evaluation
except ImportError:  # pragma: no cover - optional dependency check
    cd_evaluation = None

UNASSIGNED_TOKEN = "__UNASSIGNED__"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate clustering quality using scikit-learn/cdlib metrics."
    )
    parser.add_argument(
        "--pred",
        required=True,
        help="Path to predicted clustering assignments (one node per line).",
    )
    parser.add_argument(
        "--truth",
        required=True,
        help="Path to ground-truth clustering assignments (one node per line).",
    )
    parser.add_argument(
        "--truth-multi",
        action="store_true",
        help="Interpret ground truth as overlapping communities (zero or more labels per node).",
    )
    parser.add_argument(
        "--output",
        choices=("json", "table"),
        default="json",
        help="Choose output format (default: json).",
    )
    return parser.parse_args()


def read_indexed_assignments(path: str, allow_multi: bool) -> List[List[str]]:
    assignments: List[List[str]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            labels = line.split() if line else []

            if allow_multi:
                deduped: List[str] = []
                seen = set()
                for label in labels:
                    if label not in seen:
                        seen.add(label)
                        deduped.append(label)
                assignments.append(deduped)
            else:
                if len(labels) != 1:
                    raise ValueError(
                        f"Line {lineno} in {path} must contain exactly one cluster ID (found {len(labels)})."
                    )
                assignments.append([labels[0]])

    if not assignments:
        raise ValueError(f"No nodes found in {path}")
    return assignments


def ensure_numpy() -> None:
    if np is None:
        raise SystemExit("numpy is required but missing. Install it (and scikit-learn) before running this script.")


def ensure_sklearn() -> None:
    if sk_metrics is None:
        raise SystemExit("scikit-learn is required for this mode. Install it with 'pip install scikit-learn'.")
    ensure_numpy()


def ensure_cdlib() -> None:
    if cd_evaluation is None:
        raise SystemExit("cdlib is required for overlapping truth. Install it with 'pip install cdlib'.")


def collect_nodes(pred: List[List[str]], truth: List[List[str]]) -> List[str]:
    if len(pred) != len(truth):
        raise SystemExit(
            f"Prediction file has {len(pred)} lines but ground truth has {len(truth)}. They must match."
        )
    if not pred:
        raise SystemExit("No nodes found in either assignment file.")
    return [str(i) for i in range(len(pred))]


def to_cover(assignments: List[List[str]], nodes: Sequence[str], default_label: str) -> List[List[str]]:
    cluster_map: Dict[str, set] = defaultdict(set)
    for node, labels in zip(nodes, assignments):
        if labels:
            for label in labels:
                cluster_map[label].add(node)
        else:
            cluster_map[default_label].add(node)

    cover = []
    for members in cluster_map.values():
        if members:
            cover.append(sorted(members))

    if not cover:
        cover = [[node] for node in nodes]
    return cover


def labels_to_membership(labels: Sequence[str]) -> List[int]:
    mapping: Dict[str, int] = {}
    membership: List[int] = []
    next_id = 0
    for label in labels:
        if label not in mapping:
            mapping[label] = next_id
            next_id += 1
        membership.append(mapping[label])
    return membership


def single_label_metrics(
    truth_assignments: List[List[str]],
    pred_assignments: List[List[str]],
) -> Dict[str, float]:
    ensure_sklearn()

    y_true: List[str] = []
    y_pred: List[str] = []
    for truth_label, pred_label in zip(truth_assignments, pred_assignments):
        y_pred.append(pred_label[0] if pred_label else UNASSIGNED_TOKEN)
        y_true.append(truth_label[0] if truth_label else UNASSIGNED_TOKEN)

    metrics: Dict[str, float] = {
        "adjusted_rand_index": sk_metrics.adjusted_rand_score(y_true, y_pred),
        "adjusted_mutual_information": sk_metrics.adjusted_mutual_info_score(y_true, y_pred),
        "normalized_mutual_information": sk_metrics.normalized_mutual_info_score(
            y_true, y_pred, average_method="geometric"
        ),
        "homogeneity": sk_metrics.homogeneity_score(y_true, y_pred),
        "completeness": sk_metrics.completeness_score(y_true, y_pred),
        "v_measure": sk_metrics.v_measure_score(y_true, y_pred),
        "fowlkes_mallows": sk_metrics.fowlkes_mallows_score(y_true, y_pred),
    }

    contingency = sk_metrics.cluster.contingency_matrix(y_true, y_pred, sparse=False)
    total = contingency.sum()
    if total > 0:
        metrics["purity"] = float(np.max(contingency, axis=0).sum() / total)
        metrics["inverse_purity"] = float(np.max(contingency, axis=1).sum() / total)
    else:
        metrics["purity"] = math.nan
        metrics["inverse_purity"] = math.nan

    if ig is not None:
        membership_true = labels_to_membership(y_true)
        membership_pred = labels_to_membership(y_pred)
        try:
            metrics["igraph_nmi"] = ig.compare_communities(membership_true, membership_pred, method="nmi")
            metrics["igraph_vi"] = ig.compare_communities(membership_true, membership_pred, method="vi")
            metrics["igraph_split_join"] = ig.compare_communities(
                membership_true, membership_pred, method="split-join"
            )
        except Exception as exc:  # pragma: no cover - defensive
            metrics["igraph_error"] = float("nan")
            sys.stderr.write(f"[WARN] igraph comparison failed: {exc}\n")

    return metrics


def overlapping_metrics(
    truth_assignments: List[List[str]],
    pred_assignments: List[List[str]],
    nodes: Sequence[str],
) -> Dict[str, float]:
    ensure_cdlib()

    truth_cover = to_cover(truth_assignments, nodes, "__truth_unassigned__")
    pred_cover = to_cover(pred_assignments, nodes, "__pred_unassigned__")

    metrics: Dict[str, float] = {}
    metrics["onmi_lfk"] = cd_evaluation.overlapping_normalized_mutual_information_LFK(
        truth_cover, pred_cover
    ).score
    metrics["onmi_gce"] = cd_evaluation.overlapping_normalized_mutual_information_GCE(
        truth_cover, pred_cover
    ).score
    metrics["omega_index"] = cd_evaluation.omega_index(truth_cover, pred_cover).score
    return metrics


def unique_labels(assignments: List[List[str]]) -> int:
    return len({label for labels in assignments for label in labels})


def main() -> None:
    args = parse_args()

    try:
        pred_assignments = read_indexed_assignments(args.pred, allow_multi=False)
        truth_assignments = read_indexed_assignments(args.truth, allow_multi=args.truth_multi)
    except ValueError as exc:
        raise SystemExit(str(exc))

    nodes = collect_nodes(pred_assignments, truth_assignments)
    summary = {
        "num_nodes": len(nodes),
        "pred_clusters": unique_labels(pred_assignments),
        "truth_clusters": unique_labels(truth_assignments),
        "truth_mode": "overlapping" if args.truth_multi else "single",
    }

    if args.truth_multi:
        metrics = overlapping_metrics(truth_assignments, pred_assignments, nodes)
    else:
        metrics = single_label_metrics(truth_assignments, pred_assignments)

    summary["metrics"] = metrics

    if args.output == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Nodes: {summary['num_nodes']}")
        print(f"Predicted clusters: {summary['pred_clusters']}")
        print(f"Truth clusters: {summary['truth_clusters']}")
        print(f"Truth mode: {summary['truth_mode']}")
        print("Metrics:")
        for key in sorted(metrics):
            value = metrics[key]
            if isinstance(value, float):
                print(f"  {key}: {value:.6f}")
            else:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
