"""VieClus memetic graph clustering, on the shared harness (CLI binary).

VieClus (Biedermann, Henzinger, Schulz & Schuster, "Memetic Graph Clustering",
SEA 2018; KaHIP/VieClus) is a memetic (evolutionary) algorithm that maximises
modularity. It is the anytime baseline this survey grew out of.

We drive the CLI binary rather than the pip wheel, because the wheel hides two
features we want and the binary exposes both as-is (the log flag was merely
commented out of the argument table; vieclus.patch re-enables it):
  * Parallelism -- VieClus parallelises the evolutionary search across MPI ranks,
    so --threads maps to `mpirun -n <threads>`.
  * Time-of-best -- with --mh_print_log each rank writes a (timestamp, objective)
    convergence log; we record when the best modularity was first reached as
    time_to_best_seconds, plus the full trajectory, since a fixed time budget is
    otherwise a meaningless "runtime" for an anytime solver.

Graph I/O is binary CSR: a compat patch teaches KaHIP's reader to consume our
CBCSRv1 format directly, and VieClus writes the clustering as one cluster id per
line in node order (EVAL's format) to --output_filename. Each run executes in its
own scratch subdir because the log filename depends only on rank/seed (not the
graph name), so shared dirs would collide. EVAL provides the quality numbers.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

VIECLUS = str(Path(__file__).resolve().parent / "vieclus")


def parse_convergence(rundir, seed):
    """Reads VieClus's per-rank convergence logs for this run.

    Each log line is "<elapsed_seconds> <objective>", appended as new bests are
    found (so objective is non-decreasing). Returns (time_to_best, best_objective,
    trajectory): best_objective is the max across ranks, time_to_best is the
    earliest timestamp at which it was reached (not the final flush at the time
    limit), and trajectory is the merged (t, obj) points sorted by time.
    """
    points = []
    for log in glob.glob(os.path.join(rundir, f"log__m_rank_*_file__seed_{seed}_k_1")):
        try:
            with open(log) as f:
                for ln in f:
                    parts = ln.split()
                    if len(parts) == 2:
                        points.append((float(parts[0]), float(parts[1])))
        except OSError:
            continue
    if not points:
        return None, None, []
    points.sort()
    best_obj = max(o for _, o in points)
    t_best = min(t for t, o in points if o >= best_obj)
    return t_best, best_obj, points


def main():
    p = argparse.ArgumentParser(description="Run VieClus clustering (CLI).")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run evolutionary budget")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--threads", type=int, default=1, help="MPI ranks (mpirun -n)")
    p.add_argument("--leiden", action="store_true",
                   help="use VieClus's Leiden mode (guarantees connected communities)")
    p.add_argument("--leiden-theta", type=float, default=0.01)
    args = p.parse_args()

    graph = os.path.abspath(args.graph)
    ranks = max(1, args.threads)
    hard_timeout = (args.time * 1.5 + 60) if args.time > 0 else None

    for i in range(args.runs):
        seed = args.seed + i
        out_txt = os.path.abspath(f"{args.output_prefix}{i}.txt")
        report = {"run": i, "seed": seed, "ranks": ranks, "leiden": args.leiden}

        # Isolated cwd: the log filename depends only on rank/seed/k, so runs
        # sharing a directory would overwrite each other's logs.
        rundir = f"{args.output_prefix}{i}_vcwork"
        shutil.rmtree(rundir, ignore_errors=True)
        os.makedirs(rundir, exist_ok=True)

        # --oversubscribe: launch the requested number of ranks even when it
        # exceeds the slots OpenMPI counts (it counts physical cores by default,
        # so -n on a hyperthreaded box otherwise errors out). The rank count is
        # the user's choice via --threads; honour it.
        argv = [
            "mpirun", "--oversubscribe", "-n", str(ranks), VIECLUS, graph,
            f"--time_limit={args.time if args.time > 0 else 1.0}",
            f"--seed={seed}",
            f"--output_filename={out_txt}",
            "--mh_print_log",
        ]
        if args.leiden:
            argv += ["--leiden", f"--leiden_theta={args.leiden_theta}"]

        start = time.perf_counter()
        try:
            # No start_new_session here: mpirun must stay in this driver's
            # process group so that when the harness hard-kills the solver group
            # (ctrl-c, watchdog, or timeout) the signal reaches mpirun and its
            # ranks too. Isolating it in a new session orphaned mpirun, leaving it
            # running after the harness died. subprocess.run's own timeout still
            # kills mpirun directly, which cleans up its ranks.
            proc = subprocess.run(
                argv, cwd=rundir,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=hard_timeout,
            )
            elapsed = time.perf_counter() - start

            modularity = None
            for line in proc.stdout.splitlines():
                if line.startswith("modularity"):
                    try:
                        modularity = float(line.split()[-1])
                    except (IndexError, ValueError):
                        pass
            t_best, log_best, trajectory = parse_convergence(rundir, seed)

            if proc.returncode != 0 or not os.path.exists(out_txt):
                report["status"] = "error"
                report["error"] = (
                    f"vieclus exit {proc.returncode}: "
                    f"{proc.stdout.strip()[-500:]} {proc.stderr.strip()[-500:]}"
                )
            else:
                report["status"] = "ok"
                report["iterations"] = {"done": 1, "requested": 1}
            report["solve_seconds"] = round(elapsed, 6)
            if modularity is not None:
                report["modularity"] = modularity
            if t_best is not None:
                report["time_to_best_seconds"] = round(t_best, 6)
                report["log_best_objective"] = log_best
                report["convergence"] = [[round(t, 6), o] for t, o in trajectory]
        except subprocess.TimeoutExpired:
            report["status"] = "tle"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            report["status"] = "error"
            report["error"] = f"{type(exc).__name__}: {exc}"
            report["solve_seconds"] = round(time.perf_counter() - start, 6)
        finally:
            shutil.rmtree(rundir, ignore_errors=True)

        with open(f"{args.output_prefix}{i}.json", "w") as f:
            json.dump(report, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
