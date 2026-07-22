"""Hollocou streaming community detection, on the shared harness.

Hollocou, Bonald, Lelarge & Lemonnier, "A Streaming Algorithm for Graph
Clustering" (NeurIPS workshop, 2017). The `streamcom` binary processes the edge
stream in one pass, aggregating nodes into communities whose volume never
exceeds a threshold vmax -- vmax is the sole granularity knob, larger values
giving fewer, coarser communities.

Provenance: the upstream binary is built unchanged except for one compat patch
(hollocou.patch) that teaches its graph reader to consume our binary CSR format
directly, so the harness never converts the graph to an edge-list file on disk.
This driver is the harness adapter: it reads n from the CSR header, runs
streamcom once per requested run (enforcing the per-run time limit itself, since
streamcom has none), maps streamcom's community-per-line output into an n-length
membership file, and writes a JSON report per run. EVAL provides the quality
numbers, so we do not recompute modularity here.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

STREAMCOM = str(Path(__file__).resolve().parent / "streamcom")


def csr_num_nodes(path):
    """Reads n from a binary CSR header (8-byte magic, then int64 n)."""
    with open(path, "rb") as f:
        head = f.read(16)
    if not head.startswith(b"CBCSRv1"):
        raise SystemExit(f"{path} is not a binary CSR file; run CONVERT first")
    return int.from_bytes(head[8:16], "little", signed=True)


def read_membership(comm_file, n):
    """streamcom writes one community per line (space-separated node ids).

    Builds an n-length membership list; nodes that streamcom never placed
    (degree-0 isolates) each become their own singleton cluster, so the output
    always covers all n nodes as EVAL expects.
    """
    membership = [-1] * n
    c = 0
    with open(comm_file) as f:
        for line in f:
            ids = line.split()
            if not ids:
                continue
            for tok in ids:
                membership[int(tok)] = c
            c += 1
    for u in range(n):
        if membership[u] == -1:
            membership[u] = c
            c += 1
    return membership, c


def write_membership(path, membership):
    with open(path, "w") as f:
        f.write("\n".join(str(x) for x in membership))
        f.write("\n")


def main():
    p = argparse.ArgumentParser(description="Run Hollocou streaming clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--vmax", type=int, default=10000, help="maximum community volume")
    p.add_argument("--condition", type=int, default=0, help="aggregation: 0=AND, 1=OR")
    args = p.parse_args()

    n = csr_num_nodes(args.graph)

    for i in range(args.runs):
        seed = args.seed + i
        out_i = f"{args.output_prefix}stream_{i}"
        report = {
            "run": i,
            "seed": seed,
            "vmax": args.vmax,
            "condition": args.condition,
        }

        argv = [
            STREAMCOM,
            "-f", args.graph,
            "-o", out_i,
            "--vmax-start", str(args.vmax),
            "--vmax-end", str(args.vmax),
            "-c", str(args.condition),
            "--seed", str(seed),
            "--niter", "1",
        ]

        start = time.perf_counter()
        try:
            proc = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=args.time if args.time > 0 else None,
                start_new_session=True,
            )
            elapsed = time.perf_counter() - start

            # streamcom reports its own algorithm timing in milliseconds; prefer
            # it for solve_seconds, falling back to the measured wall time.
            algo_ms = None
            for line in proc.stdout.splitlines():
                if line.startswith("Algorithm time:"):
                    algo_ms = float(line.split()[-2])
            report["solve_seconds"] = round(
                algo_ms / 1000.0 if algo_ms is not None else elapsed, 6
            )

            comm_file = f"{out_i}_0_{args.vmax}"
            if proc.returncode != 0 or not os.path.exists(comm_file):
                report["status"] = "error"
                report["error"] = (
                    f"streamcom exit {proc.returncode}: "
                    f"{proc.stdout.strip()[-500:]} {proc.stderr.strip()[-500:]}"
                )
            else:
                membership, k = read_membership(comm_file, n)
                write_membership(f"{args.output_prefix}{i}.txt", membership)
                report["status"] = "ok"
                report["n_clusters"] = k
                report["iterations"] = {"done": 1, "requested": 1}
        except subprocess.TimeoutExpired:
            report["status"] = "tle"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            report["status"] = "error"
            report["error"] = f"{type(exc).__name__}: {exc}"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
        finally:
            # streamcom's aux output (community-per-line) is only an
            # intermediate; drop it however the run ended.
            try:
                os.unlink(f"{out_i}_0_{args.vmax}")
            except OSError:
                pass

        with open(f"{args.output_prefix}{i}.json", "w") as f:
            json.dump(report, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
