"""Walktrap clustering via python-igraph, on the shared harness.

Walktrap (Pons & Latapy, "Computing communities in large networks using random
walks", 2005) agglomerates communities using a random-walk distance between
vertices; igraph's community_walktrap computes the dendrogram, cut here at
maximum modularity. The random-walk length `steps` is the method's one
hyperparameter (the paper explores it; 4 is the standard value). Walktrap is
deterministic, so repeated runs differ only in timing.

Mirrors the Louvain/CNM migration: binary CSR via scripts/graphio.py, a SIGALRM
per-run timeout, and a JSON report per run. The pre-migration version is kept as
run_walktrap_legacy.py.
"""

import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import igraph as ig  # noqa: E402,F401
import graphio  # noqa: E402


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


def main():
    p = argparse.ArgumentParser(description="Run Walktrap clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--steps", type=int, default=4, help="random-walk length t")
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    g = csr.to_igraph()
    parse_seconds = time.perf_counter() - t0

    weights = g.es["weight"] if "weight" in g.edge_attributes() else None

    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        # Walktrap is deterministic; the seed is recorded only for report parity.
        report = {
            "run": i,
            "seed": args.seed + i,
            "parse_seconds": round(parse_seconds, 6),
            "steps": args.steps,
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time)

        start = time.perf_counter()
        try:
            dendrogram = g.community_walktrap(weights=weights, steps=args.steps)
            clusters = dendrogram.as_clustering()  # cut at maximum modularity
            elapsed = time.perf_counter() - start
            signal.setitimer(signal.ITIMER_REAL, 0)

            report["status"] = "ok"
            report["solve_seconds"] = round(elapsed, 6)
            report["modularity"] = g.modularity(clusters.membership, weights=weights)
            report["n_clusters"] = len(clusters)
            report["iterations"] = {"done": 1, "requested": 1}

            graphio.write_clustering(f"{args.output_prefix}{i}.txt", clusters.membership)
        except RunTimeout:
            signal.setitimer(signal.ITIMER_REAL, 0)
            report["status"] = "tle"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            signal.setitimer(signal.ITIMER_REAL, 0)
            report["status"] = "error"
            report["error"] = f"{type(exc).__name__}: {exc}"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)

        with open(f"{args.output_prefix}{i}.json", "w") as f:
            json.dump(report, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
