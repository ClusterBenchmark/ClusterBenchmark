"""Bayan clustering via bayanpy, on the shared harness.

Bayan (Aref, Mostajabdaveh, Chheda, "Bayan: exact and approximate community
detection", 2024) maximises modularity with a branch-and-cut integer program
solved by Gurobi. It is exact/near-exact and therefore does not scale: it needs a
Gurobi licence, and on graphs beyond a few thousand edges it will run out of time
or memory building/solving the program -- which is a result to report, so unlike
the old driver we do not refuse large graphs, we let them fail honestly.

bayanpy has a native time budget (`time_allowed`, the Gurobi time limit) that we
map to the per-run `--time`; on timeout it returns the best partition found with a
positive optimality gap, which we record. The graph is loaded from binary CSR via
scripts/graphio.py and each run writes a JSON report. The pre-migration version is
kept as run_bayan_legacy.py.
"""

import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import networkx as nx  # noqa: E402
import bayanpy  # noqa: E402

import graphio  # noqa: E402


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


def main():
    p = argparse.ArgumentParser(description="Run Bayan clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit -> Gurobi time budget")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--resolution", type=float, default=1.0)
    p.add_argument("--threshold", type=float, default=0.001, help="optimality-gap tolerance")
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    n = csr.n
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from(csr.edges_upper().tolist())
    parse_seconds = time.perf_counter() - t0

    # Bayan's branch-and-cut takes a wall-clock budget for the solve; use the
    # per-run limit. The model-building phase before it is not time-bounded, so a
    # SIGALRM (slightly above the budget) backstops a runaway build on a graph too
    # large for the exact program, marking it tle instead of waiting for the
    # harness's much longer outer timeout.
    time_allowed = int(args.time) if args.time > 0 else 3600
    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        report = {
            "run": i,
            "seed": args.seed + i,
            "parse_seconds": round(parse_seconds, 6),
            "resolution": args.resolution,
            "threshold": args.threshold,
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time + 60)

        start = time.perf_counter()
        try:
            modularity, optimality_gap, community, modeling_time, solve_time = bayanpy.bayan(
                G, threshold=args.threshold, time_allowed=time_allowed, resolution=args.resolution
            )
            signal.setitimer(signal.ITIMER_REAL, 0)
            report["status"] = "ok"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
            report["modularity"] = modularity
            report["optimality_gap"] = optimality_gap
            report["modeling_time"] = modeling_time
            report["gurobi_solve_time"] = solve_time
            report["n_clusters"] = len(community)
            report["iterations"] = {"done": 1, "requested": 1}

            membership = [0] * n
            for c, comm in enumerate(community):
                for u in comm:
                    membership[u] = c
            graphio.write_clustering(f"{args.output_prefix}{i}.txt", membership)
        except RunTimeout:
            signal.setitimer(signal.ITIMER_REAL, 0)
            report["status"] = "tle"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            # Gurobi licence/size limits and modelling blow-ups land here.
            signal.setitimer(signal.ITIMER_REAL, 0)
            report["status"] = "error"
            report["error"] = f"{type(exc).__name__}: {exc}"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)

        with open(f"{args.output_prefix}{i}.json", "w") as f:
            json.dump(report, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
