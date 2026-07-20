#!/usr/bin/env python3
"""Flattens harness JSONL into the legacy CSV layout.

The plotting and table code under paper/ consumes the pre-migration column
order, so this keeps that pipeline working unchanged while the JSONL remains
the source of truth.

Legacy layout:
    solver,instance,run,max_mem_kb,status,time,iterations,
    <EVAL csv: instance,n,m,modularity,numerator,n_clusters,conductance,
     cut_ratio[,f1,accuracy,tp,fp,tn,fn,ari,nmi,purity,inverse_purity]>
"""

import argparse
import csv
import json
import sys

EVAL_BASE = [
    "instance",
    "n",
    "m",
    "modularity",
    "modularity_numerator",
    "n_clusters",
    "conductance",
    "cut_ratio",
]
EVAL_LABELLED = [
    "f1",
    "accuracy",
    "tp",
    "fp",
    "tn",
    "fn",
    "ari",
    "nmi",
    "purity",
    "inverse_purity",
]

HEADER = ["solver", "instance", "run", "max_mem_kb", "status", "time", "iterations"]


def solve_seconds(record):
    report = record.get("solver_report") or {}
    for key in ("best_found_seconds", "solve_seconds"):
        if key in report:
            return report[key]
    return record.get("process", {}).get("wall_seconds")


def iterations(record):
    report = record.get("solver_report") or {}
    it = report.get("iterations")
    if isinstance(it, dict):
        return it.get("done", 0)
    return it if it is not None else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("jsonl", nargs="+")
    p.add_argument("--out", default=None, help="output CSV, default stdout")
    p.add_argument("--header", action="store_true", help="emit a header row")
    p.add_argument(
        "--protocol", default=None, help="only export records with this protocol label"
    )
    args = p.parse_args()

    out = open(args.out, "w", newline="") if args.out else sys.stdout
    writer = csv.writer(out)

    labelled = False
    rows = []
    for path in args.jsonl:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if args.protocol and r.get("protocol") != args.protocol:
                    continue

                mem = r.get("memory", {}).get("peak_bytes")
                row = [
                    r["solver"],
                    r["instance"],
                    r["run"] + 1,  # legacy runs were 1-indexed
                    "" if mem is None else mem // 1024,
                    r.get("process", {}).get("exit_code", ""),
                    solve_seconds(r),
                    iterations(r),
                ]

                q = r.get("quality")
                if q is None:
                    # Legacy behaviour: a failed run emitted only the prefix.
                    rows.append(row)
                    continue

                row.extend(q.get(k, "") for k in EVAL_BASE)
                if any(k in q for k in EVAL_LABELLED):
                    labelled = True
                    row.extend(q.get(k, "") for k in EVAL_LABELLED)
                rows.append(row)

    if args.header:
        header = HEADER + EVAL_BASE + (EVAL_LABELLED if labelled else [])
        writer.writerow(header)
    writer.writerows(rows)

    if args.out:
        out.close()


if __name__ == "__main__":
    main()
