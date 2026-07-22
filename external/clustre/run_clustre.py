"""CluStRE streaming graph clustering, on the shared harness.

CluStRE (Fischer, Gottesbüren et al., "CluStRE: Streaming Graph Clustering with
Multi-Stage Refinement", 2025). A streaming clusterer that builds a quotient
graph while streaming nodes and optimises modularity, with optional in-memory
refinement (the VieClus memetic algorithm) and re-streaming local search. This
driver serves both operating points via --mode:

    light   one-pass streaming              -> clustre-fast
    strong  streaming + VieClus + restream  -> clustre-strong

Ingest: CluStRE reads its own graph formats, and its binary reader is seek-based
(so it cannot consume a pipe). Rather than deep-patch that reader, we convert our
binary CSR to CluStRE's native ParHIP binary format (a seekable binary CSR it
already supports) into the scratch workdir, run against it, and delete it -- a
transient temp, not a persistent per-solver copy of the dataset. CluStRE writes
the clustering as one cluster id per line in node order, exactly EVAL's format,
so --output_filename targets {prefix}{i}.txt directly. EVAL provides quality.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import numpy as np  # noqa: E402
import graphio  # noqa: E402

CLUSTRE = str(Path(__file__).resolve().parent / "clustre")


def csr_to_parhip(csr_path, bin_path):
    """Writes our binary CSR as a ParHIP binary graph (version 3, unweighted).

    ParHIP layout, all little-endian uint64: header [version=3, n, 2m], then
    n+1 vertex offsets as absolute byte positions, then 2m edge targets. Edges
    are streamed in chunks so the whole array never lands in RAM at once. Returns
    (n, m) with m the number of directed edges (= 2 * undirected).
    """
    csr = graphio.load_csr(csr_path)
    n, m = csr.n, csr.m
    V = csr.V  # int64 memmap, length n+1, cumulative directed-edge offsets
    E = csr.E  # int32 memmap, length m
    edges_start = 3 * 8 + (n + 1) * 8  # first byte after header + offset table
    with open(bin_path, "wb") as f:
        np.array([3, n, m], dtype=np.uint64).tofile(f)
        offsets = np.uint64(edges_start) + V.astype(np.uint64) * np.uint64(8)
        offsets.tofile(f)
        chunk = 1 << 23
        for s in range(0, m, chunk):
            E[s : s + chunk].astype(np.uint64).tofile(f)
    return n, m


def main():
    p = argparse.ArgumentParser(description="Run CluStRE clustering.")
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--mode", default="light",
                   choices=("light", "light_plus", "evo", "strong"))
    p.add_argument("--one-pass-algorithm", default="modularity")
    p.add_argument("--ext-algorithm-time", type=int, default=300,
                   help="VieClus budget in s (strong/evo); capped by --time")
    p.add_argument("--ls-time-limit", type=int, default=600,
                   help="local-search budget in s (light_plus/strong); capped by --time")
    p.add_argument("--cut-off", type=float, default=0.05,
                   help="local-search modularity-gain stop fraction")
    p.add_argument("--cluster-fraction", type=float, default=0.0,
                   help="cap initial clusters at fraction*n; 0 leaves the default")
    args = p.parse_args()

    outdir = str(Path(args.output_prefix).parent) + "/"
    bin_path = f"{args.output_prefix}input.bin"

    t0 = time.perf_counter()
    n, m = csr_to_parhip(args.graph, bin_path)
    convert_seconds = time.perf_counter() - t0

    uses_ext = args.mode in ("strong", "evo")
    uses_ls = args.mode in ("strong", "light_plus")
    # Refinement budgets: VieClus (ext) and restream local search (ls) each get
    # up to the per-run --time, but they must finish *before* the hard subprocess
    # kill or the solver is SIGKILLed with nothing written. So the internal
    # budgets are capped at --time, and the hard kill is set generously above the
    # sum of the phases that actually run (plus streaming/I-O margin). In
    # practice cut_off stops local search early, so wall time is closer to the
    # ext budget than to this backstop.
    cap = int(args.time) if args.time > 0 else None
    ext_budget = min(args.ext_algorithm_time, cap) if cap else args.ext_algorithm_time
    ls_budget = min(args.ls_time_limit, cap) if cap else args.ls_time_limit
    if args.time > 0:
        phase_sum = (ext_budget if uses_ext else 0) + (ls_budget if uses_ls else 0)
        hard_timeout = (phase_sum if phase_sum else cap) * 1.5 + 120
    else:
        hard_timeout = None

    try:
        for i in range(args.runs):
            seed = args.seed + i
            out_txt = f"{args.output_prefix}{i}.txt"
            report = {
                "run": i,
                "seed": seed,
                "mode": args.mode,
                "convert_seconds": round(convert_seconds, 6),
            }

            argv = [
                CLUSTRE, bin_path,
                f"--seed={seed}",
                f"--one_pass_algorithm={args.one_pass_algorithm}",
                f"--mode={args.mode}",
                f"--output_filename={out_txt}",
                f"--output_path={outdir}",
            ]
            if args.cluster_fraction > 0:
                argv.append(f"--cluster_fraction={args.cluster_fraction}")
            if uses_ext:
                argv += [f"--ext_clustering_algorithm=VieClus", f"--ext_algorithm_time={ext_budget}"]
            if uses_ls:
                argv += [f"--ls_time_limit={ls_budget}", f"--cut_off={args.cut_off}"]

            start = time.perf_counter()
            try:
                proc = subprocess.run(
                    argv,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=hard_timeout,
                    start_new_session=True,
                )
                elapsed = time.perf_counter() - start

                total_s = None
                for line in proc.stdout.splitlines():
                    if line.startswith("Total Time:"):
                        try:
                            total_s = float(line.split()[2])
                        except (IndexError, ValueError):
                            pass
                report["solve_seconds"] = round(
                    total_s if total_s is not None else elapsed, 6
                )

                if proc.returncode != 0 or not os.path.exists(out_txt):
                    report["status"] = "error"
                    report["error"] = (
                        f"clustre exit {proc.returncode}: "
                        f"{proc.stdout.strip()[-500:]} {proc.stderr.strip()[-500:]}"
                    )
                else:
                    report["status"] = "ok"
                    report["iterations"] = {"done": 1, "requested": 1}
            except subprocess.TimeoutExpired:
                report["status"] = "tle"
                report["solve_seconds"] = round(time.perf_counter() - start, 6)
            except Exception as exc:  # noqa: BLE001 - reported, not swallowed
                report["status"] = "error"
                report["error"] = f"{type(exc).__name__}: {exc}"
                report["solve_seconds"] = round(time.perf_counter() - start, 6)

            with open(f"{args.output_prefix}{i}.json", "w") as f:
                json.dump(report, f)
    finally:
        # Drop the transient ParHIP graph and CluStRE's per-run FlatBuffer stats
        # files (named after the input stem), keeping only the harness artifacts.
        for stray in glob.glob(f"{args.output_prefix}input*.bin"):
            try:
                os.unlink(stray)
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
