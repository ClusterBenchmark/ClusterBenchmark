"""Leiden clustering via python-igraph, on the shared harness.

Leiden (Traag, Waltman & van Eck, "From Louvain to Leiden: guaranteeing
well-connected communities", 2019) with the modularity objective (igraph's
community_leiden defaults to CPM; we set modularity, since the survey is about
modularity). The resolution gamma is the tuned granularity knob (like Louvain);
n_iterations is a compute knob -- igraph's default is 2; Protocol B can set it to
-1 to run until the partition is stable.

Mirrors the Louvain migration: binary CSR via scripts/graphio.py, a SIGALRM
per-run timeout, and a JSON report per run. Leiden is stochastic, so igraph's RNG
is seeded per run. The pre-migration version is kept as run_leiden_legacy.py.
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
    p = argparse.ArgumentParser(description="Run Leiden clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--resolution", type=float, default=1.0)
    p.add_argument("--n-iterations", type=int, default=2, help="-1 runs until stable")
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    g = csr.to_igraph()
    parse_seconds = time.perf_counter() - t0

    weights = g.es["weight"] if "weight" in g.edge_attributes() else None

    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        # igraph draws from Python's global RNG; seed it so each run reproduces.
        seed = args.seed + i
        random.seed(seed)
        ig.set_random_number_generator(random)

        report = {
            "run": i,
            "seed": seed,
            "parse_seconds": round(parse_seconds, 6),
            "resolution": args.resolution,
            "n_iterations": args.n_iterations,
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time)

        start = time.perf_counter()
        try:
            clusters = g.community_leiden(
                objective_function="modularity",
                weights=weights,
                resolution=args.resolution,
                n_iterations=args.n_iterations,
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
