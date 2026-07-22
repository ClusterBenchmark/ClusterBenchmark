"""VieClus memetic graph clustering, on the shared harness.

VieClus (Biedermann, Henzinger, Schulz & Schuster, "Memetic Graph Clustering",
SEA 2018; KaHIP/VieClus) is a memetic (evolutionary) algorithm that maximises
modularity. It is an anytime solver: given a time budget it keeps evolving a pool
of clusterings and returns the best found. It was the reference baseline this
survey grew out of.

Integration uses VieClus's official Python interface (pip install vieclus), which
exposes cluster(vwgt, xadj, adjcwgt, adjncy, seed, time_limit) over CSR arrays and
returns (modularity, membership). Our binary CSR maps straight onto those arrays
via scripts/graphio.py -- no METIS text, no on-disk conversion, no output parsing.
The pip wheel is single-process (no MPI island parallelism); the harness runs it
at one thread, so this is the single-thread VieClus baseline.

Note on time: VieClus is anytime, so solve_seconds here is essentially the budget
it was given, not a time-to-solution. Capturing when the best clustering was
actually found (VieClus already logs improving incumbents) is deferred future
work; for now --time is the evolutionary budget.
"""

import argparse
import contextlib
import json
import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import numpy as np  # noqa: E402
import graphio  # noqa: E402
import vieclus  # noqa: E402

INT32_MAX = 2**31 - 1


class RunTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise RunTimeout()


@contextlib.contextmanager
def suppress_fd_stdout():
    """Redirects file descriptor 1 to /dev/null.

    VieClus prints per-generation "fingerprint" lines from C++ even when its
    suppress_output flag is set, which would otherwise accumulate megabytes of
    noise on a long run. Redirect at the fd level so the C++ prints are dropped;
    stderr is left alone so real errors still surface.
    """
    saved = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        yield
    finally:
        os.dup2(saved, 1)
        os.close(devnull)
        os.close(saved)


def main():
    p = argparse.ArgumentParser(description="Run VieClus clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run evolutionary budget")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--leiden", action="store_true",
                   help="use VieClus's Leiden mode (guarantees connected communities)")
    p.add_argument("--leiden-theta", type=float, default=0.01,
                   help="Leiden refinement temperature (only with --leiden)")
    p.add_argument("--cluster-upperbound", type=int, default=0,
                   help="max cluster size, 0 = no limit")
    args = p.parse_args()

    t0 = time.perf_counter()
    csr = graphio.load_csr(args.graph)
    n, m = csr.n, csr.m
    if m > INT32_MAX:
        raise SystemExit(
            f"VieClus uses 32-bit edge ids; {m} directed edges exceed {INT32_MAX}"
        )

    # VieClus's C interface takes int arrays (int* xadj/adjncy/vwgt/adjcwgt).
    xadj = np.asarray(csr.V, dtype=np.int32)
    adjncy = np.asarray(csr.E, dtype=np.int32)
    vwgt = csr.VW.astype(np.int32) if csr.VW is not None else np.ones(n, dtype=np.int32)
    adjcwgt = csr.EW.astype(np.int32) if csr.EW is not None else np.ones(m, dtype=np.int32)
    parse_seconds = time.perf_counter() - t0

    # VieClus honours time_limit internally; SIGALRM is only a backstop against a
    # run that ignores it (as Bayan does), a little above the budget.
    signal.signal(signal.SIGALRM, _alarm)

    for i in range(args.runs):
        seed = args.seed + i
        report = {
            "run": i,
            "seed": seed,
            "parse_seconds": round(parse_seconds, 6),
            "leiden": args.leiden,
            "cluster_upperbound": args.cluster_upperbound,
        }

        if args.time > 0:
            signal.setitimer(signal.ITIMER_REAL, args.time + 60)

        start = time.perf_counter()
        try:
            with suppress_fd_stdout():
                modularity, clustering = vieclus.cluster(
                    vwgt, xadj, adjcwgt, adjncy,
                    suppress_output=True,
                    seed=seed,
                    time_limit=args.time if args.time > 0 else 1.0,
                    cluster_upperbound=args.cluster_upperbound,
                    leiden=args.leiden,
                    leiden_theta=args.leiden_theta,
                )
            signal.setitimer(signal.ITIMER_REAL, 0)

            membership = list(clustering)
            report["status"] = "ok"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
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
