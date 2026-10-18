#!/usr/bin/env python3
"""Process raw JSONL benchmark results into clean CSV files for plots and tables in paper/data/."""

import csv
import json
from collections import defaultdict
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = PAPER_DIR.parent
DATA_DIR = PAPER_DIR / "data"

# The 16 non-exact benchmarked solvers in display order (top to bottom in horizontal strip plots)
# Grouped by Classical (top 9) vs Learning-based (bottom 7), ordered by modularity strength within each group:
PLOTTED_SOLVERS = [
    ("vieclus", "vieclus", "VieClus", "classical"),
    ("leiden", "leiden", "Leiden", "classical"),
    ("louvain", "louvain", "Louvain", "classical"),
    ("combo", "combo", "COMBO", "classical"),
    ("cnm", "cnm", "CNM", "classical"),
    ("infomap", "infomap", "Infomap", "classical"),
    ("walktrap", "walktrap", "Walktrap", "classical"),
    ("clustre-fast", "clustre_fast", "CluStRE", "classical"),
    ("hollocou", "hollocou", "Hollocou", "classical"),
    ("gnns", "gnns", "GNNS", "learned"),
    ("dgcluster", "dgcluster", "DGCluster", "learned"),
    ("magi-sage", "magi", "MAGI", "learned"),
    ("lim", "lim", "LIM", "learned"),
    ("dmon", "dmon", "DMoN", "learned"),
    ("ucode", "ucode", "UCoDe", "learned"),
    ("commdgi", "commdgi", "CommDGI", "learned"),
]

ALL_SOLVERS = [(r, p) for r, p, _, _ in PLOTTED_SOLVERS] + [
    ("bayan", "bayan"),
    ("magi", "magi_gcn"),
]

GT_INSTANCES = [
    "cora",
    "citeseer",
    "amazon_photo",
    "amazon_computers",
    "coauthor_cs",
    "pubmed",
    "coauthor_physics",
    "ogbn-arxiv",
    "reddit",
    "ogbn-products",
]

DIMACS_INSTANCES = [
    "karate",
    "chesapeake",
    "dolphins",
    "lesmis",
    "polbooks",
    "adjnoun",
    "football",
    "jazz",
    "celegansneural",
    "celegans_metabolic",
    "email",
    "polblogs",
    "netscience",
    "power",
    "hep-th",
    "PGPgiantcompo",
    "astro-ph",
    "cond-mat",
    "as-22july06",
    "cond-mat-2003",
    "cond-mat-2005",
    "preferentialAttachment",
    "smallworld",
    "G_n_pin_pout",
    "caidaRouterLevel",
    "cnr-2000",
    "eu-2005",
    "in-2004",
    "road_central",
    "uk-2002",
    "road_usa",
    "uk-2007-05",
]


def load_protocol_a_dir(result_dir: Path):
    """Load all JSONL records from a Protocol A directory and aggregate per (solver, instance)."""
    records = defaultdict(lambda: defaultdict(list))
    for jsonl_path in sorted(result_dir.glob("*.jsonl")):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                records[r["solver"]][r["instance"]].append(r)
    return records


def summarize_solver_instance(runs):
    """Given the 5 runs for a (solver, instance) pair, return the summary dict."""
    ok_runs = [
        r
        for r in runs
        if r.get("status") == "ok" and (r.get("quality") or {}).get("modularity") is not None
    ]
    if ok_runs:
        best_mod = max((r["quality"].get("modularity") or -1.0) for r in ok_runs)
        nmi_vals = [r["quality"].get("nmi") for r in ok_runs if r["quality"].get("nmi") is not None]
        f1_vals = [r["quality"].get("f1") for r in ok_runs if r["quality"].get("f1") is not None]
        best_nmi = max(nmi_vals) if nmi_vals else None
        best_f1 = max(f1_vals) if f1_vals else None

        solve_times = [
            (r.get("solver_report") or {}).get("solve_seconds")
            for r in ok_runs
            if (r.get("solver_report") or {}).get("solve_seconds") is not None
        ]
        mean_time = sum(solve_times) / len(solve_times) if solve_times else None

        peak_mbs = [
            (r.get("memory") or {}).get("peak_mb")
            for r in ok_runs
            if (r.get("memory") or {}).get("peak_mb") is not None
        ]
        max_peak_mb = max(peak_mbs) if peak_mbs else None

        iters_done = []
        iters_req = []
        for r in ok_runs:
            it = (r.get("solver_report") or {}).get("iterations") or {}
            if it.get("done") is not None:
                iters_done.append(it["done"])
            if it.get("requested") is not None:
                iters_req.append(it["requested"])
        max_iter_done = max(iters_done) if iters_done else None
        max_iter_req = max(iters_req) if iters_req else None

        q0 = ok_runs[0].get("quality") or {}
        return {
            "status": "OK",
            "n_ok": len(ok_runs),
            "n": q0.get("n"),
            "m": q0.get("m") // 2 if q0.get("m") else None,
            "modularity": best_mod,
            "nmi": best_nmi,
            "f1": best_f1,
            "solve_seconds": mean_time,
            "peak_mb": max_peak_mb,
            "iter_done": max_iter_done,
            "iter_req": max_iter_req,
        }

    statuses = [r.get("status", "") for r in runs]
    oom = any((r.get("memory") or {}).get("oom_killed") for r in runs)
    peak_mbs = [
        (r.get("memory") or {}).get("peak_mb")
        for r in runs
        if (r.get("memory") or {}).get("peak_mb") is not None
    ]
    max_peak = max(peak_mbs) if peak_mbs else 0.0
    wall_secs = [
        (r.get("process") or {}).get("wall_seconds")
        for r in runs
        if (r.get("process") or {}).get("wall_seconds") is not None
    ]
    max_wall = max(wall_secs) if wall_secs else 0.0
    err_texts = " ".join(
        str((r.get("solver_report") or {}).get("error", "")) + " " + str(r.get("stderr_tail", ""))
        for r in runs
    )
    mem_keywords = (
        "MemoryError",
        "bad_alloc",
        "ResourceExhaustedError",
        "DefaultCPUAllocator",
        "CUDA out of memory",
        "OutOfMemoryError",
        "Unable to allocate",
        "Cannot use GPU when output.shape",
    )
    if (
        oom
        or "oom" in statuses
        or "mle" in statuses
        or max_peak >= 120000.0
        or any(k in err_texts for k in mem_keywords)
    ):
        fail_status = "MLE"
    elif (
        "tle" in statuses
        or any((r.get("process") or {}).get("outer_timeout") for r in runs)
        or any((r.get("process") or {}).get("watchdog_killed_run") is not None for r in runs)
        or max_wall >= 3600.0
    ):
        fail_status = "TLE"
    else:
        fail_status = "ERR"

    return {
        "status": fail_status,
        "n_ok": 0,
        "n": None,
        "m": None,
        "modularity": None,
        "nmi": None,
        "f1": None,
        "solve_seconds": None,
        "peak_mb": max_peak if peak_mbs else None,
        "iter_done": None,
        "iter_req": None,
    }


def write_summary_csv(records, instances, out_csv: Path):
    """Write a tidy summary CSV of best scores, runtime, memory, and status per (solver, instance)."""
    fieldnames = [
        "solver",
        "plot_name",
        "instance",
        "status",
        "n_ok",
        "modularity",
        "nmi",
        "f1",
        "solve_seconds",
        "peak_mb",
        "iter_done",
        "iter_req",
    ]
    rows = []
    for raw_name, plot_name in ALL_SOLVERS:
        for inst in instances:
            runs = records.get(raw_name, {}).get(inst, [])
            s = summarize_solver_instance(runs) if runs else {"status": "MISSING", "n_ok": 0}
            rows.append({
                "solver": raw_name,
                "plot_name": plot_name,
                "instance": inst,
                "status": s.get("status"),
                "n_ok": s.get("n_ok"),
                "modularity": f"{s['modularity']:.6f}" if s.get("modularity") is not None else "",
                "nmi": f"{s['nmi']:.6f}" if s.get("nmi") is not None else "",
                "f1": f"{s['f1']:.6f}" if s.get("f1") is not None else "",
                "solve_seconds": f"{s['solve_seconds']:.4f}" if s.get("solve_seconds") is not None else "",
                "peak_mb": f"{s['peak_mb']:.2f}" if s.get("peak_mb") is not None else "",
                "iter_done": s.get("iter_done") if s.get("iter_done") is not None else "",
                "iter_req": s.get("iter_req") if s.get("iter_req") is not None else "",
            })
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def piecewise_u(tau: float, split: float = 0.90) -> float:
    """Map tau in [0, 1] to u in [0, 1] where [split, 1.0] occupies [0.0, 0.5] and [0.0, split] occupies [0.5, 1.0]."""
    tau = max(0.0, min(1.0, tau))
    if tau >= split:
        return 0.5 * (1.0 - tau) / (1.0 - split)
    return 0.5 + 0.5 * (split - tau) / split


def write_strip_wide_csv(records, instances, metric: str, out_csv: Path, split: float = 0.90):
    """Write wide-format horizontal strip-plot CSV with columns u_<alg>, y_<alg>, tau_<alg>, plus fail_u, fail_y.

    Each row i in 0..N-1 corresponds to the i-th solved instance of that algorithm.
    Unresolved (TLE/MLE) instances are also recorded in uf_<alg>, yf_<alg> inside the [1.05, 1.15] Fail band.
    """
    n_inst = len(instances)
    n_solvers = len(PLOTTED_SOLVERS)
    scores = defaultdict(dict)
    opt_per_inst = {}

    for inst in instances:
        best_on_inst = 0.0
        for raw_name, plot_name, _, _ in PLOTTED_SOLVERS:
            runs = records.get(raw_name, {}).get(inst, [])
            s = summarize_solver_instance(runs) if runs else {"status": "MISSING"}
            val = s.get(metric)
            if val is not None and s.get("status") == "OK":
                val = max(0.0, val)
                scores[plot_name][inst] = val
                if val > best_on_inst:
                    best_on_inst = val
        opt_per_inst[inst] = best_on_inst

    alg_points = {}
    alg_fails = {}
    for idx, (raw_name, plot_name, label, paradigm) in enumerate(PLOTTED_SOLVERS):
        y_center = n_solvers - idx  # 16 down to 1
        solved_items = []
        n_failed = 0
        for inst in instances:
            val = scores[plot_name].get(inst)
            opt = opt_per_inst.get(inst, 0.0)
            if val is not None and opt > 0.0:
                solved_items.append((val / opt, inst))
            else:
                n_failed += 1
        solved_items.sort(key=lambda x: (-x[0], x[1]))

        k = len(solved_items)
        pts = []
        for j, (tau, inst) in enumerate(solved_items):
            if k <= 1:
                dy = 0.0
            else:
                step = 3 if k <= 10 else 7
                while step > 1 and (k % step == 0):
                    step += 1
                slot = ((j * step) % k) / (k - 1)
                dy = -0.25 + 0.50 * slot
            u = piecewise_u(tau, split=split)
            pts.append((f"{u:.6f}", f"{y_center + dy:.4f}", f"{tau:.6f}"))
        while len(pts) < n_inst:
            pts.append(("", "", ""))
        alg_points[plot_name] = pts

        fail_pts = []
        for j in range(n_failed):
            if n_failed == 1:
                dy = 0.0
                du = 1.10
            else:
                slot = j / (n_failed - 1)
                dy = -0.24 + 0.48 * slot
                du = 1.06 + 0.08 * ((j % 3) / 2.0)
            fail_pts.append((f"{du:.6f}", f"{y_center + dy:.4f}"))
        while len(fail_pts) < n_inst:
            fail_pts.append(("", ""))
        alg_fails[plot_name] = fail_pts

    fieldnames = ["idx"]
    for _, plot_name, _, _ in PLOTTED_SOLVERS:
        fieldnames.extend([
            f"u_{plot_name}",
            f"y_{plot_name}",
            f"tau_{plot_name}",
            f"uf_{plot_name}",
            f"yf_{plot_name}",
        ])

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(n_inst):
            row = {"idx": i}
            for _, plot_name, _, _ in PLOTTED_SOLVERS:
                u_s, y_s, t_s = alg_points[plot_name][i]
                uf_s, yf_s = alg_fails[plot_name][i]
                row[f"u_{plot_name}"] = u_s
                row[f"y_{plot_name}"] = y_s
                row[f"tau_{plot_name}"] = t_s
                row[f"uf_{plot_name}"] = uf_s
                row[f"yf_{plot_name}"] = yf_s
            writer.writerow(row)


def write_efficiency_csv(rw_records, dimacs_records, out_csv: Path):
    """Write geometric-mean efficiency and quality summary per solver across Ground-Truth and DIMACS."""
    import math

    def gmean(xs):
        return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None

    rows = []
    for raw_name, plot_name, label, paradigm in PLOTTED_SOLVERS:
        gt_mods, gt_nmis, gt_f1s, gt_us, gt_mems = [], [], [], [], []
        for inst in GT_INSTANCES:
            s = summarize_solver_instance(rw_records.get(raw_name, {}).get(inst, []))
            if s.get("status") == "OK" and (s.get("modularity") or 0) > 0 and s.get("solve_seconds") and s.get("m"):
                gt_mods.append(s["modularity"])
                if (s.get("nmi") or 0) > 0:
                    gt_nmis.append(s["nmi"])
                if (s.get("f1") or 0) > 0:
                    gt_f1s.append(s["f1"])
                gt_us.append((s["solve_seconds"] * 1e6) / s["m"])
                if s.get("peak_mb"):
                    gt_mems.append(s["peak_mb"])

        dim_mods, dim_us, dim_mems = [], [], []
        for inst in DIMACS_INSTANCES:
            s = summarize_solver_instance(dimacs_records.get(raw_name, {}).get(inst, []))
            if s.get("status") == "OK" and (s.get("modularity") or 0) > 0 and s.get("solve_seconds") and s.get("m"):
                dim_mods.append(s["modularity"])
                dim_us.append((s["solve_seconds"] * 1e6) / s["m"])
                if s.get("peak_mb"):
                    dim_mems.append(s["peak_mb"])

        rows.append({
            "solver": raw_name,
            "plot_name": plot_name,
            "label": label,
            "paradigm": paradigm,
            "gt_solved": len(gt_mods),
            "gt_us_per_edge": f"{gmean(gt_us):.4f}" if gt_us else "",
            "gt_modularity": f"{gmean(gt_mods):.4f}" if gt_mods else "",
            "gt_nmi": f"{gmean(gt_nmis):.4f}" if gt_nmis else "",
            "gt_f1": f"{gmean(gt_f1s):.4f}" if gt_f1s else "",
            "gt_peak_mb": f"{gmean(gt_mems):.2f}" if gt_mems else "",
            "dimacs_solved": len(dim_mods),
            "dimacs_us_per_edge": f"{gmean(dim_us):.4f}" if dim_us else "",
            "dimacs_modularity": f"{gmean(dim_mods):.4f}" if dim_mods else "",
            "dimacs_peak_mb": f"{gmean(dim_mems):.2f}" if dim_mems else "",
        })

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_protocol_s_csv(rw_records, scale_dir: Path, out_csv: Path):
    """Write Protocol S scaling comparison (1T CPU vs 32T CPU vs RTX 4090 GPU) on Ground-Truth graphs."""
    scale_recs = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for p in sorted(scale_dir.glob("*.jsonl")):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                mode = f"{r.get('device', 'cpu')}_{r.get('threads', 1)}"
                scale_recs[r["solver"]][mode][r["instance"]].append(r)

    scale_solvers = [
        ("vieclus", "VieClus"),
        ("gnns", "GNNS"),
        ("dgcluster", "DGCluster"),
        ("magi-sage", "MAGI"),
        ("lim", "LIM"),
        ("dmon", "DMoN"),
        ("ucode", "UCoDe"),
        ("commdgi", "CommDGI"),
        ("magi", "MAGI-GCN"),
    ]
    rows = []
    for raw_name, label in scale_solvers:
        for inst in GT_INSTANCES:
            s1 = summarize_solver_instance(rw_records.get(raw_name, {}).get(inst, []))
            s32 = summarize_solver_instance(scale_recs[raw_name]["cpu_32"].get(inst, [])) if scale_recs[raw_name]["cpu_32"].get(inst) else {"status": "MISSING"}
            sgpu = summarize_solver_instance(scale_recs[raw_name]["cuda_32"].get(inst, [])) if scale_recs[raw_name]["cuda_32"].get(inst) else {"status": "MISSING"}
            t1 = s1.get("solve_seconds")
            t32 = s32.get("solve_seconds")
            tgpu = sgpu.get("solve_seconds")
            rows.append({
                "solver": raw_name,
                "label": label,
                "instance": inst,
                "status_1t": s1.get("status"),
                "time_1t": f"{t1:.2f}" if t1 is not None else s1.get("status", ""),
                "mod_1t": f"{s1['modularity']:.4f}" if s1.get("modularity") is not None else "",
                "iter_1t": f"{s1['iter_done']}/{s1['iter_req']}" if s1.get("iter_done") is not None else "",
                "status_32t": s32.get("status"),
                "time_32t": f"{t32:.2f}" if t32 is not None else s32.get("status", ""),
                "mod_32t": f"{s32['modularity']:.4f}" if s32.get("modularity") is not None else "",
                "iter_32t": f"{s32['iter_done']}/{s32['iter_req']}" if s32.get("iter_done") is not None else "",
                "speedup_32t": f"{t1 / t32:.2f}" if (t1 and t32) else "",
                "status_gpu": sgpu.get("status"),
                "time_gpu": f"{tgpu:.2f}" if tgpu is not None else sgpu.get("status", ""),
                "mod_gpu": f"{sgpu['modularity']:.4f}" if sgpu.get("modularity") is not None else "",
                "iter_gpu": f"{sgpu['iter_done']}/{sgpu['iter_req']}" if sgpu.get("iter_done") is not None else "",
                "speedup_gpu": f"{t1 / tgpu:.2f}" if (t1 and tgpu) else "",
            })
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_protocol_b_csv(rw_records, scale_dir: Path, params_dir: Path, out_csv: Path):
    """Write Protocol B hyperparameter tuning comparison on Cora, Citeseer, and Pubmed."""
    scale_recs = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for p in sorted(scale_dir.glob("*.jsonl")):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                mode = f"{r.get('device', 'cpu')}_{r.get('threads', 1)}"
                scale_recs[r["solver"]][mode][r["instance"]].append(r)

    tune_solvers = [
        ("leiden", "Leiden", "classical"),
        ("louvain", "Louvain", "classical"),
        ("combo", "COMBO", "classical"),
        ("walktrap", "Walktrap", "classical"),
        ("clustre-strong", "CluStRE-Strong", "classical"),
        ("hollocou", "Hollocou", "classical"),
        ("gnns", "GNNS", "learned"),
        ("dgcluster", "DGCluster", "learned"),
        ("magi-sage", "MAGI", "learned"),
        ("magi", "MAGI-GCN", "learned"),
        ("lim", "LIM", "learned"),
        ("dmon", "DMoN", "learned"),
        ("ucode", "UCoDe", "learned"),
        ("commdgi", "CommDGI", "learned"),
    ]
    rows = []
    for raw_name, label, paradigm in tune_solvers:
        row = {"solver": raw_name, "label": label, "paradigm": paradigm}
        for inst in ["cora", "citeseer", "pubmed"]:
            s1 = summarize_solver_instance(rw_records.get(raw_name, {}).get(inst, []))
            s32 = summarize_solver_instance(scale_recs[raw_name]["cpu_32"].get(inst, [])) if scale_recs[raw_name]["cpu_32"].get(inst) else {}
            q_def_1t = s1.get("modularity")
            q_def_32t = s32.get("modularity")
            # For fixed-k GNNs where tuning used k=sqrt(n) (same as Protocol S), record both 1T and 32T default baselines
            q_base = q_def_32t if q_def_32t is not None else q_def_1t
            meta_file = params_dir / f"{raw_name}.{inst}.meta.json"
            q_tun = None
            if meta_file.exists():
                d = json.loads(meta_file.read_text(encoding="utf-8"))
                val = d.get("best_value")
                if val is not None and val > 1e-6:
                    q_tun = val
            row[f"{inst}_def_1t"] = f"{q_def_1t:.4f}" if q_def_1t is not None else ""
            row[f"{inst}_def_32t"] = f"{q_def_32t:.4f}" if q_def_32t is not None else ""
            row[f"{inst}_tuned"] = f"{q_tun:.4f}" if q_tun is not None else ""
            row[f"{inst}_delta_1t"] = f"{q_tun - q_def_1t:+.4f}" if (q_tun is not None and q_def_1t is not None) else ""
            row[f"{inst}_delta_base"] = f"{q_tun - q_base:+.4f}" if (q_tun is not None and q_base is not None) else ""
        rows.append(row)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_adc_sbm_csvs(adc_dir: Path, dout_csv: Path, sigma_csv: Path):
    """Export ADC-SBM synthetic sweeps (dout and sigma_c) from results_adc_sbm/*.jsonl."""
    adc_solvers = [
        ("vieclus", "vieclus"),
        ("leiden", "leiden"),
        ("gnns", "gnns"),
        ("dgcluster", "dgcluster"),
        ("magi-sage", "magi"),
        ("magi", "magi_gcn"),
        ("dmon", "dmon"),
        ("commdgi", "commdgi"),
        ("ucode", "ucode"),
        ("lim", "lim"),
    ]
    dout_rows = defaultdict(dict)
    sigma_rows = defaultdict(dict)

    for raw_name, col_name in adc_solvers:
        p = adc_dir / f"{raw_name}.jsonl"
        if not p.exists():
            continue
        by_inst = defaultdict(list)
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                by_inst[r["instance"]].append(r)
        for inst, runs in by_inst.items():
            ok_nmis = [
                r["quality"]["nmi"]
                for r in runs
                if r.get("status") == "ok" and (r.get("quality") or {}).get("nmi") is not None
            ]
            best_nmi = max(ok_nmis) if ok_nmis else 0.0
            if inst.startswith("dout_"):
                val = float(inst.replace("dout_", ""))
                dout_rows[val][col_name] = best_nmi
            elif inst.startswith("sigma_"):
                val = float(inst.replace("sigma_", ""))
                sigma_rows[val][col_name] = best_nmi

    col_names = [c for _, c in adc_solvers]
    with open(dout_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dout"] + col_names)
        writer.writeheader()
        for val in sorted(dout_rows.keys()):
            row = {"dout": f"{val:.2f}"}
            for c in col_names:
                row[c] = f"{dout_rows[val].get(c, 0.0):.6f}"
            writer.writerow(row)

    with open(sigma_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sigma"] + col_names)
        writer.writeheader()
        for val in sorted(sigma_rows.keys()):
            row = {"sigma": f"{val:.6f}"}
            for c in col_names:
                row[c] = f"{sigma_rows[val].get(c, 0.0):.6f}"
            writer.writerow(row)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rw_records = load_protocol_a_dir(ROOT_DIR / "results_real_world")
    dimacs_records = load_protocol_a_dir(ROOT_DIR / "results_dimacs")

    write_summary_csv(rw_records, GT_INSTANCES, DATA_DIR / "prot_a_real_world_summary.csv")
    write_summary_csv(dimacs_records, DIMACS_INSTANCES, DATA_DIR / "prot_a_dimacs_summary.csv")

    write_strip_wide_csv(rw_records, GT_INSTANCES, "modularity", DATA_DIR / "prot_a_gt_modularity_strip.csv", split=0.90)
    write_strip_wide_csv(dimacs_records, DIMACS_INSTANCES, "modularity", DATA_DIR / "prot_a_dimacs_modularity_strip.csv", split=0.90)
    write_strip_wide_csv(rw_records, GT_INSTANCES, "nmi", DATA_DIR / "prot_a_gt_nmi_strip.csv", split=0.85)
    write_strip_wide_csv(rw_records, GT_INSTANCES, "f1", DATA_DIR / "prot_a_gt_f1_strip.csv", split=0.90)

    write_efficiency_csv(rw_records, dimacs_records, DATA_DIR / "prot_a_efficiency.csv")
    write_protocol_s_csv(rw_records, ROOT_DIR / "out_scale", DATA_DIR / "prot_s_scaling.csv")
    write_protocol_b_csv(rw_records, ROOT_DIR / "out_scale", ROOT_DIR / "params", DATA_DIR / "prot_b_tuning.csv")
    write_adc_sbm_csvs(
        ROOT_DIR / "results_adc_sbm",
        DATA_DIR / "adc_sbm_dout.csv",
        DATA_DIR / "adc_sbm_sigma.csv",
    )

    print("Successfully generated all paper CSV datasets in paper/data/.")


if __name__ == "__main__":
    main()

