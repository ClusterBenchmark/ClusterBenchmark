"""CNM (Clauset-Newman-Moore) clustering via python-igraph, on the shared harness.

CNM greedily agglomerates communities to maximise modularity -- igraph's
community_fastgreedy, the algorithm from Clauset, Newman & Moore, "Finding
community structure in very large networks" (Phys. Rev. E 2004). It is
deterministic and has no hyperparameters, so repeated runs differ only in timing.

Mirrors the Louvain migration: the graph is loaded from binary CSR via
scripts/graphio.py, the per-run timeout uses SIGALRM in-process, and each run
writes a JSON report next to its clustering. The pre-migration version (cdlib /
networkx greedy_modularity with a forked worker for the timeout) is kept as
run_cnm_legacy.py.
"""

import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import igraph as ig  # noqa: E402,F401  (availability check; also seeds parity)
import graphio  # noqa: E402


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


def main():
    p = argparse.ArgumentParser(description="Run CNM (fast greedy) clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    g = csr.to_igraph()
    parse_seconds = time.perf_counter() - t0

    weights = g.es["weight"] if "weight" in g.edge_attributes() else None

    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        # CNM is deterministic; the seed is recorded only for report parity.
        report = {
            "run": i,
            "seed": args.seed + i,
            "parse_seconds": round(parse_seconds, 6),
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time)

        start = time.perf_counter()
        try:
            dendrogram = g.community_fastgreedy(weights=weights)
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
