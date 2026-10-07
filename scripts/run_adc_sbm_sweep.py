#!/usr/bin/env python3
"""ADC-SBM Synthetic Graph Experiment Runner.

Generates synthetic graphs under controlled signal degradation:
  1. Topology degradation: sweep d_out in [1.0, 14.0] with sigma_c = 3.0.
  2. Feature degradation:  sweep sigma_c in [0.01, 10.0] with d_out = 2.0.

Instances are stored in /tmp/adc_sbm/ (.csr, .feat, .labels).
Each solver runs on the EXACT same prepared instance files via harness.py.
Outputs land in results_adc_sbm/<solver>.jsonl.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import gen_adc_sbm  # noqa: E402
import graphio      # noqa: E402

TMP_DIR = Path("/tmp/adc_sbm")
RESULTS_DIR = REPO_ROOT / "results_adc_sbm"
CONVERT_BIN = REPO_ROOT / "CONVERT"
HARNESS_PY = REPO_ROOT / "scripts" / "harness.py"

def get_grid(dense=True):
    if dense:
        # 53 points for d_out (step 0.25) to cleanly capture the steep phase transition
        dout_values = [round(x, 2) for x in np.arange(1.0, 14.05, 0.25)]
        # 61 points for sigma_c (step 0.05 in log10)
        sigma_exps = [j / 20.0 for j in range(-40, 21)]
        sigma_values = [round(float(10.0 ** exp), 4) for exp in sigma_exps]
    else:
        # Standard 27 points (step 0.5)
        dout_values = [round(x, 1) for x in np.arange(1.0, 14.1, 0.5)]
        # Standard 31 points (step 0.1 in log10)
        sigma_exps = [j / 10.0 for j in range(-20, 11)]
        sigma_values = [round(float(10.0 ** exp), 4) for exp in sigma_exps]
    return dout_values, sigma_values


def generate_and_convert(name, n=1000, k=4, avg_deg=20.0, assortativity=0.9,
                         dim=32, feature_signal=3.0, feature_std=1.0, seed=42):
    """Generates an instance and creates .csr, .feat, and .labels in TMP_DIR."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    csr_path = TMP_DIR / f"{name}.csr"
    feat_path = TMP_DIR / f"{name}.feat"
    labels_path = TMP_DIR / f"{name}.labels"
    graph_tmp = TMP_DIR / f"{name}.graph"

    if csr_path.exists() and feat_path.exists() and labels_path.exists():
        return csr_path, feat_path, labels_path

    print(f"Generating synthetic instance: {name} ...")
    A, X, z = gen_adc_sbm.make_adc_sbm(
        n=n,
        k=k,
        avg_degree=avg_deg,
        assortativity=assortativity,
        feature_dim=dim,
        feature_signal=feature_signal,
        feature_std=feature_std,
        seed=seed,
    )

    gen_adc_sbm.write_metis_graph(str(graph_tmp), A)
    gen_adc_sbm.write_labels(str(labels_path), z)
    graphio.write_features(str(feat_path), X)

    # Convert to canonical binary CSR
    cmd = [str(CONVERT_BIN), str(graph_tmp), str(csr_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if graph_tmp.exists():
        graph_tmp.unlink()

    return csr_path, feat_path, labels_path


def load_completed_instances(jsonl_path):
    """Returns a set of instance names that already have 5 runs in the jsonl."""
    if not jsonl_path.exists():
        return set()
    counts = {}
    with open(jsonl_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                    inst = r.get("instance")
                    if inst:
                        counts[inst] = counts.get(inst, 0) + 1
                except Exception:
                    continue
    return {inst for inst, cnt in counts.items() if cnt >= 5}


def main():
    p = argparse.ArgumentParser(description="Run ADC-SBM sweep experiments.")
    p.add_argument("--runs", type=int, default=5, help="Number of repetitions per point")
    p.add_argument("--dense", action=argparse.BooleanOptionalAction, default=True,
                   help="Use high-density grid (53 dout points, 61 sigma points) vs coarse (27/31)")
    p.add_argument("--threads", type=int, default=16, help="Threads for GNN solvers")
    p.add_argument("--vieclus-time", type=float, default=5.0, help="Per-run time limit for VieClus (s)")
    p.add_argument("--gnn-time", type=float, default=60.0, help="Per-run time limit for GNNs (s)")
    p.add_argument("--mem", type=float, default=120.0, help="Memory limit in GB")
    p.add_argument("--solvers", default="vieclus,leiden,dmon,commdgi,gnns,dgcluster,magi,magi-sage,ucode,lim",
                   help="Comma-separated solver list")
    args = p.parse_args()

    solvers = [s.strip() for s in args.solvers.split(",") if s.strip()]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    dout_values, sigma_values = get_grid(dense=args.dense)
    print(f"Sweep Grid: {'Dense' if args.dense else 'Standard'} ({len(dout_values)} d_out points, {len(sigma_values)} sigma_c points)")

    # Step 1: Prepare all instances
    instances = []

    # Sweep 1: d_out
    for dout in dout_values:
        name = f"dout_{dout:05.2f}"
        assortativity = (20.0 - dout) / 20.0
        csr, feat, lbl = generate_and_convert(
            name,
            n=1000,
            k=4,
            avg_deg=20.0,
            assortativity=assortativity,
            dim=32,
            feature_signal=3.0,
            feature_std=1.0,
            seed=int(dout * 100) + 1,
        )
        instances.append((name, csr, feat, lbl))

    # Sweep 2: sigma_c
    for sigma in sigma_values:
        name = f"sigma_{sigma:07.4f}"
        assortativity = (20.0 - 2.0) / 20.0  # d_out = 2.0 fixed
        csr, feat, lbl = generate_and_convert(
            name,
            n=1000,
            k=4,
            avg_deg=20.0,
            assortativity=assortativity,
            dim=32,
            feature_signal=sigma,
            feature_std=1.0,
            seed=int(sigma * 1000) + 9999,
        )
        instances.append((name, csr, feat, lbl))

    print(f"\nAll {len(instances)} synthetic instances prepared in {TMP_DIR}")
    print(f"Target Solvers: {solvers}")

    # Step 2: Execute benchmark harness
    for s in solvers:
        out_jsonl = RESULTS_DIR / f"{s}.jsonl"
        completed = load_completed_instances(out_jsonl)

        is_vieclus = (s == "vieclus")
        is_leiden = (s == "leiden")

        time_limit = args.vieclus_time if is_vieclus else args.gnn_time
        threads = 1 if (is_vieclus or is_leiden) else args.threads
        device = "cpu"

        print(f"\n[{s}] Starting runs (threads={threads}, time={time_limit}s, dev={device}) ...")

        for name, csr, feat, lbl in instances:
            if name in completed:
                continue

            harness_cmd = [
                sys.executable,
                str(HARNESS_PY),
                "--solver", s,
                "--graph", str(csr),
                "--features", str(feat),
                "--labels", str(lbl),
                "--clusters", "4",
                "--runs", str(args.runs),
                "--time", str(time_limit),
                "--memory", str(args.mem),
                "--threads", str(threads),
                "--device", device,
                "--protocol", "adc_sbm",
                "--out", str(out_jsonl),
            ]

            print(f"  -> {s} / {name}")
            subprocess.run(harness_cmd, check=True)

    print("\nADC-SBM sweeps successfully completed! Results in results_adc_sbm/")


if __name__ == "__main__":
    main()
