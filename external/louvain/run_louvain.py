"""Louvain clustering via python-igraph, driven by the shared harness.

Differences from the pre-migration version (kept as run_louvain_legacy.py):

  * The graph is loaded from the binary CSR format through scripts/graphio.py
    instead of being parsed in Python. The old parser built a Python list of
    (u, v) tuples, costing roughly 130 bytes per edge before igraph made its
    own copy, which dominated both runtime and peak memory on large instances.

  * The per-run timeout uses SIGALRM in this process rather than forking a
    worker through multiprocessing. Forking made memory accounting ambiguous,
    since parent and child share copy-on-write pages.

  * Each run writes a JSON report next to its clustering, so the harness never
    has to parse positional fields out of stdout.
"""

import argparse
import json
import random
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import igraph as ig  # noqa: E402
import graphio  # noqa: E402


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


def main():
    p = argparse.ArgumentParser(description="Run Louvain clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--resolution", type=float, default=1.0)
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    g = csr.to_igraph()
    parse_seconds = time.perf_counter() - t0

    weights = g.es["weight"] if "weight" in g.edge_attributes() else None

    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        # igraph draws from Python's global RNG, so seeding it makes each run
        # reproducible. Without this, tuning partly optimises RNG luck rather
        # than the parameter, since run-to-run spread exceeds the effect size.
        seed = args.seed + i
        random.seed(seed)
        ig.set_random_number_generator(random)

        report = {
            "run": i,
            "seed": seed,
            "parse_seconds": round(parse_seconds, 6),
            "resolution": args.resolution,
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time)

        start = time.perf_counter()
        try:
            clusters = g.community_multilevel(
                weights=weights, resolution=args.resolution
            )
            elapsed = time.perf_counter() - start
            signal.setitimer(signal.ITIMER_REAL, 0)

            report["status"] = "ok"
            report["solve_seconds"] = round(elapsed, 6)
            report["modularity"] = g.modularity(
                clusters.membership, weights=weights, resolution=args.resolution
            )
            report["n_clusters"] = len(clusters)
            report["iterations"] = {"done": 1, "requested": 1}

            graphio.write_clustering(
                f"{args.output_prefix}{i}.txt", clusters.membership
            )
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
