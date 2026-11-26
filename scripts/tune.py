#!/usr/bin/env python3
"""Generic hyperparameter tuning for any solver with a solver.json.

One tuner serves every solver, classical and learning based alike, because the
search space is declared as data and the harness already emits a uniform
record per run. This is what makes the two benchmarking protocols comparable:
the tuned configuration is produced the same way for Louvain as for DMoN.

    python3 scripts/tune.py --solver louvain \\
        --graphs tuning/*.csr --metric modularity --trials 100 \\
        --out params/louvain.dimacs.json

A trial evaluates one configuration on every tuning graph and optimises the
aggregate (geometric mean by default, matching how the paper aggregates across
instances). Failed runs receive the worst possible score rather than being
skipped, so a configuration that crashes or exceeds a limit is penalised
instead of silently disappearing from the average.

Tuning graphs should be disjoint from the evaluation set when the tuned result
is presented as a generalising configuration. When it is presented as an upper
bound, tuning directly on the evaluation instances is intentional and should be
recorded as such via --protocol.
"""

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / "scripts" / "harness.py"

# Metrics where larger is better. Conductance and cut ratio are minimised.
MAXIMISE = {
    "modularity",
    "nmi",
    "ari",
    "f1",
    "accuracy",
    "purity",
    "inverse_purity",
}
MINIMISE = {"conductance", "cut_ratio"}


def suggest(trial, name, spec):
    kind = spec.get("type", "float")
    if kind == "categorical":
        return trial.suggest_categorical(name, spec["choices"])
    if kind == "bool":
        return trial.suggest_categorical(name, [False, True])

    low, high = spec["range"]
    log = spec.get("scale") == "log"
    if kind == "int":
        return trial.suggest_int(name, int(low), int(high), log=log)
    return trial.suggest_float(name, float(low), float(high), log=log)


def run_once(solver_path, graph, config, args, jsonl_path):
    argv = [
        sys.executable,
        str(HARNESS),
        "--solver",
        str(solver_path),
        "--graph",
        str(graph),
        "--runs",
        str(args.runs),
        "--time",
        str(args.time),
        "--memory",
        str(args.memory),
        "--threads",
        str(args.threads),
        "--device",
        args.device,
        "--protocol",
        "tuning",
        "--out",
        str(jsonl_path),
        "--workdir",
        str(args.workdir),
    ]
    argv += ["--clusters", str(args.clusters)]
    if args.features_suffix:
        candidate = Path(str(graph).rsplit(".", 1)[0] + args.features_suffix)
        if candidate.exists():
            argv += ["--features", str(candidate)]
    for name, value in config.items():
        argv += ["--set", f"{name}={value}"]

    subprocess.run(argv, capture_output=True, text=True)

    records = []
    if jsonl_path.exists():
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        jsonl_path.unlink()
    return records


def score_records(records, metric, worst):
    """Best score over runs for one instance, or worst if all runs failed."""
    values = [
        r["quality"][metric]
        for r in records
        if r.get("status") == "ok" and metric in r.get("quality", {})
    ]
    if not values:
        return worst
    return max(values) if metric in MAXIMISE else min(values)


def aggregate(scores, how, metric):
    if not scores:
        return 0.0
    if how == "mean":
        return sum(scores) / len(scores)
    if how == "min":
        return min(scores) if metric in MAXIMISE else max(scores)
    # Geometric mean, shifted so that non-positive scores stay well defined.
    shift = 1e-6
    adjusted = [max(s, 0.0) + shift for s in scores]
    return math.exp(sum(math.log(a) for a in adjusted) / len(adjusted)) - shift


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--solver", required=True)
    p.add_argument("--graphs", nargs="+", required=True, help="tuning instances")
    p.add_argument("--metric", default="modularity")
    p.add_argument("--aggregate", default="geomean", choices=("geomean", "mean", "min"))
    p.add_argument("--trials", type=int, default=50)
    p.add_argument("--timeout", type=float, default=None, help="total tuning budget in seconds")
    p.add_argument("--runs", type=int, default=1, help="runs per instance per trial")
    p.add_argument("--time", type=float, default=3600.0, help="per-run limit")
    p.add_argument("--memory", type=float, default=250.0)
    p.add_argument("--threads", type=int, default=16)
    p.add_argument("--clusters", default="auto", help="cluster count or 'auto' (harness derives from cluster_policy)")
    p.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    p.add_argument("--features-suffix", default=None, help="e.g. .features")
    p.add_argument("--workdir", default=".cb_work")
    p.add_argument("--out", required=True, help="overlay json to write")
    p.add_argument("--study-db", default=None, help="sqlite url for a resumable study")
    args = p.parse_args()

    try:
        import optuna
    except ImportError:
        raise SystemExit(
            "optuna is required.\n"
            "  python3 -m venv scripts/.venv && scripts/.venv/bin/pip install optuna\n"
            "  scripts/.venv/bin/python3 scripts/tune.py ..."
        )

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from harness import resolve_solver

    solver_path = resolve_solver(args.solver)
    solver = json.loads(solver_path.read_text())
    # A param with "tunable": false is still forwarded by the harness (so it can
    # be set per graph class), but is held at its default during a search rather
    # than consuming a search dimension.
    specs = {
        name: spec
        for name, spec in solver.get("params", {}).items()
        if spec.get("tunable", True)
    }
    if not specs:
        raise SystemExit(f"{solver['name']} exposes no tunable parameters")

    if args.metric in MAXIMISE:
        direction, worst = "maximize", 0.0
    elif args.metric in MINIMISE:
        direction, worst = "minimize", 1.0
    else:
        raise SystemExit(f"unknown metric '{args.metric}'")

    Path(args.workdir).mkdir(parents=True, exist_ok=True)
    graphs = [Path(g).resolve() for g in args.graphs]
    for g in graphs:
        if not g.exists():
            raise SystemExit(f"missing tuning graph {g}")

    print(
        f"tuning {solver['name']} on {len(graphs)} instance(s), "
        f"metric={args.metric} ({direction}), {args.trials} trials",
        file=sys.stderr,
    )

    def objective(trial):
        config = {name: suggest(trial, name, spec) for name, spec in specs.items()}
        scores = []
        for i, graph in enumerate(graphs):
            with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
                jsonl_path = Path(tf.name)
            records = run_once(solver_path, graph, config, args, jsonl_path)
            s = score_records(records, args.metric, worst)
            scores.append(s)
            trial.report(aggregate(scores, args.aggregate, args.metric), i)
            if trial.should_prune():
                raise optuna.TrialPruned()
        return aggregate(scores, args.aggregate, args.metric)

    study = optuna.create_study(
        direction=direction,
        pruner=optuna.pruners.MedianPruner(n_warmup_steps=1),
        storage=args.study_db,
        study_name=f"{solver['name']}-{args.metric}",
        load_if_exists=bool(args.study_db),
    )
    study.optimize(objective, n_trials=args.trials, timeout=args.timeout)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(study.best_params, indent=2, sort_keys=True) + "\n")

    print(f"best {args.metric}: {study.best_value:.6f}", file=sys.stderr)
    print(f"wrote {out_path}", file=sys.stderr)
    for name, value in sorted(study.best_params.items()):
        print(f"  {name} = {value}", file=sys.stderr)

    # Provenance next to the overlay, so a tuned configuration is auditable.
    meta = {
        "solver": solver["name"],
        "metric": args.metric,
        "aggregate": args.aggregate,
        "direction": direction,
        "trials_requested": args.trials,
        "trials_completed": len(study.trials),
        "best_value": study.best_value,
        "tuning_graphs": [g.name for g in graphs],
        "per_run_time_limit": args.time,
        "memory_limit_gb": args.memory,
        "device": args.device,
        "threads": args.threads,
    }
    out_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
