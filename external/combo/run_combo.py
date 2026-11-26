"""Combo clustering via pycombo, on the shared harness.

Combo (Sobolevsky, Campari, Belyi, Ratti, "General optimization technique for
high-quality community detection in complex networks", 2014) is a strong
modularity optimiser. It is stochastic, so it takes a seed, and it exposes the
generalised-modularity resolution as its one hyperparameter (1.0 is standard
modularity), tuned like Louvain's.

Mirrors the Louvain/CNM migration: binary CSR via scripts/graphio.py, a SIGALRM
per-run timeout, and a JSON report per run. pycombo works on a networkx graph;
the pre-migration cdlib wrapper is kept as run_combo_legacy.py.
"""

import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import networkx as nx  # noqa: E402
import pycombo  # noqa: E402

import graphio  # noqa: E402


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


def main():
    p = argparse.ArgumentParser(description="Run Combo clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--resolution", type=float, default=1.0)
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    n = csr.n
    G = nx.Graph()
    G.add_nodes_from(range(n))
    w = csr.weights_upper()
    if w is not None:
        G.add_weighted_edges_from(
            (int(u), int(v), float(wt))
            for (u, v), wt in zip(csr.edges_upper().tolist(), w.tolist())
        )
        weight = "weight"
    else:
        G.add_edges_from(csr.edges_upper().tolist())
        weight = None
    parse_seconds = time.perf_counter() - t0

    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        seed = args.seed + i
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
            partition, modularity = pycombo.execute(
                G,
                weight=weight,
                modularity_resolution=args.resolution,
                random_seed=seed,
                return_modularity=True,
            )
            elapsed = time.perf_counter() - start
            signal.setitimer(signal.ITIMER_REAL, 0)

            membership = [partition[v] for v in range(n)]

            report["status"] = "ok"
            report["solve_seconds"] = round(elapsed, 6)
            report["modularity"] = modularity
            report["n_clusters"] = len(set(membership))
            report["iterations"] = {"done": 1, "requested": 1}

            graphio.write_clustering(f"{args.output_prefix}{i}.txt", membership)
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
