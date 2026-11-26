"""Infomap clustering via the infomap package, on the shared harness.

Infomap (Rosvall & Bergstrom, "Maps of random walks on complex networks reveal
community structure", 2008) minimises the map equation's codelength. It is
parameter-free (Markov time 1) but stochastic, so it takes a seed and an
optional number of restart trials (best codelength kept). We evaluate the
resulting partition with modularity like every other solver; the codelength is
recorded in the report for reference.

Mirrors the Louvain/CNM migration: binary CSR via scripts/graphio.py, a SIGALRM
per-run timeout, and a JSON report per run. The pre-migration version (per-edge
add_link loop, forked worker for the timeout) is kept as run_infomap_legacy.py.
"""

import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import numpy as np  # noqa: E402
from infomap import Infomap  # noqa: E402

import graphio  # noqa: E402


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


def main():
    p = argparse.ArgumentParser(description="Run Infomap clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--num-trials", type=int, default=1, help="restart trials; best codelength kept")
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    edges = np.asarray(csr.edges_upper())
    w = csr.weights_upper()
    # infomap.add_links takes a numpy array; use (k,3) with weights, else (k,2).
    if w is not None:
        links = np.column_stack([edges.astype(np.float64), np.asarray(w, dtype=np.float64)])
    else:
        links = edges
    n = csr.n
    parse_seconds = time.perf_counter() - t0

    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        seed = args.seed + i
        report = {
            "run": i,
            "seed": seed,
            "parse_seconds": round(parse_seconds, 6),
            "num_trials": args.num_trials,
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time)

        start = time.perf_counter()
        try:
            # Infomap requires a strictly positive seed, so offset the harness
            # seed (which starts at 0) by one; the mapping stays deterministic.
            im = Infomap(
                f"--flow-model undirected --silent --seed {seed + 1} "
                f"--num-trials {args.num_trials}"
            )
            im.add_links(links)
            im.run()
            elapsed = time.perf_counter() - start
            signal.setitimer(signal.ITIMER_REAL, 0)

            # Membership by module id; isolated (degree-0) vertices get their own.
            membership = [-1] * n
            for node in im.nodes:
                membership[node.node_id] = node.module_id
            nxt = (max(membership) + 1) if membership else 0
            for v in range(n):
                if membership[v] == -1:
                    membership[v] = nxt
                    nxt += 1

            report["status"] = "ok"
            report["solve_seconds"] = round(elapsed, 6)
            report["codelength"] = im.codelength
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
