#!/usr/bin/env python3
"""Shared execution harness for all clustering solvers.

Every solver exposes the same command line interface:

    run.sh --graph <file> --runs <k> --time <s> --memory <gb>
           [--threads <p>] [--clusters <c>] [--features <f>] [--labels <f>]
           [--params <json>] [--set key=value ...] [--device cpu|cuda]

Everything solver specific lives in that solver's solver.json: how to invoke
it, which of the standard arguments it understands, and which hyperparameters
it exposes together with their defaults and search ranges.

Results are written as JSON Lines, one object per run. Use export_csv.py to
produce the flat CSV layout consumed by the plotting code in paper/.

Memory is accounted with cgroup v2 rather than /usr/bin/time, so that the
quantity we limit on is the same quantity we report, the whole process tree is
covered, and copy-on-write pages are not double counted.
"""

import argparse
import glob
import json
import math
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_BIN = REPO_ROOT / "EVAL"
CONVERT_BIN = REPO_ROOT / "CONVERT"

STANDARD_IO_KEYS = (
    "graph",
    "features",
    "labels",
    "output",
    "runs",
    "timeout",
    "threads",
    "clusters",
    "memory",
    "device",
    "seed",
)


# --------------------------------------------------------------------------
# cgroup v2 memory accounting
# --------------------------------------------------------------------------


class MemoryMonitor:
    """Runs a command in its own cgroup v2 scope and samples memory usage.

    Falls back to sampling the process tree through /proc when cgroups are not
    delegated to this user. The fallback is less exact, which we record in the
    output so the two are never silently mixed.
    """

    # A systemd transient scope is destroyed the moment its last process
    # exits, so memory.peak cannot be read after the fact. Instead we wrap the
    # command in a shell that stays inside the cgroup and reads memory.peak
    # itself once the solver has finished.
    PEAK_WRAPPER = (
        '"$@"; ec=$?; '
        'rel=$(cut -d: -f3 < /proc/self/cgroup); '
        'cat "/sys/fs/cgroup$rel/memory.peak" > "$CB_PEAK_FILE" 2>/dev/null; '
        "exit $ec"
    )

    def __init__(self, memory_limit_gb, sample_hz=20.0, trace=False):
        self.memory_limit_gb = memory_limit_gb
        self.interval = 1.0 / sample_hz
        # The full memory time series is only useful for debugging the monitor
        # itself; the peak is tracked directly below. Off by default, since at
        # 20 Hz an hour-long run is ~72k samples per run of pure output clutter.
        self.trace = trace
        self.samples = []
        self.peak_bytes = None
        self.method = None
        self.oom_killed = False
        self.watchdog_killed_run = None
        self._stop = threading.Event()
        self._cgroup = None
        self._peak_file = None

    # -- cgroup discovery ---------------------------------------------------

    @staticmethod
    def cgroups_available():
        return (
            shutil.which("systemd-run") is not None
            and Path("/sys/fs/cgroup/cgroup.controllers").exists()
        )

    def _find_cgroup(self, unit):
        """Locates the scope's cgroup directory."""
        uid = os.getuid()
        candidates = [
            f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/{unit}.scope",
            f"/sys/fs/cgroup/user.slice/user-{uid}.slice/{unit}.scope",
        ]
        for c in candidates:
            if Path(c).is_dir():
                return Path(c)
        hits = glob.glob(f"/sys/fs/cgroup/**/{unit}.scope", recursive=True)
        return Path(hits[0]) if hits else None

    def _read_int(self, name):
        try:
            return int((self._cgroup / name).read_text().strip())
        except (OSError, ValueError):
            return None

    # -- sampling -----------------------------------------------------------

    def _sample_cgroup(self, t0):
        while not self._stop.is_set():
            if self._cgroup is None or not self._cgroup.is_dir():
                self._stop.wait(self.interval)
                continue
            if self.trace:
                cur = self._read_int("memory.current")
                if cur is not None:
                    self.samples.append((round(time.monotonic() - t0, 3), cur))
            # memory.peak is monotonic, so tracking it here bounds the error to
            # one sampling interval even if the wrapper's read is lost.
            peak = self._read_int("memory.peak")
            if peak is not None and (self.peak_bytes is None or peak > self.peak_bytes):
                self.peak_bytes = peak
            self._stop.wait(self.interval)

    @staticmethod
    def _proc_tree_rss(root_pid):
        """Sum of RSS over the process tree, in bytes."""
        total = 0
        stack = [root_pid]
        seen = set()
        while stack:
            pid = stack.pop()
            if pid in seen:
                continue
            seen.add(pid)
            try:
                status = Path(f"/proc/{pid}/status").read_text()
            except OSError:
                continue
            for line in status.splitlines():
                if line.startswith("VmRSS:"):
                    total += int(line.split()[1]) * 1024
                    break
            try:
                children = Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
                stack.extend(int(c) for c in children)
            except OSError:
                pass
        return total

    def _sample_proc(self, root_pid, t0):
        while not self._stop.is_set():
            rss = self._proc_tree_rss(root_pid)
            if rss > 0:
                # This path has no cgroup memory.peak, so the peak must come from
                # the samples; track it directly rather than from the trace list.
                if self.peak_bytes is None or rss > self.peak_bytes:
                    self.peak_bytes = rss
                if self.trace:
                    self.samples.append((round(time.monotonic() - t0, 3), rss))
            self._stop.wait(self.interval)

    # -- killing the solver tree -------------------------------------------

    def _kill_solver(self, proc):
        """Hard-kill the entire solver process tree.

        In cgroup mode the scope's cgroup.kill reaps every process in the scope
        at once, regardless of process group -- essential because a launcher like
        mpirun puts each rank in its own process group, so os.killpg on the
        driver's group alone leaves the ranks running. We still killpg as a
        belt-and-suspenders (and it is the only mechanism in the non-cgroup
        fallback path).
        """
        if self._cgroup is not None:
            try:
                (self._cgroup / "cgroup.kill").write_text("1")
            except OSError:
                pass
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            try:
                proc.kill()
            except OSError:
                pass

    # -- per-run hard timeout ----------------------------------------------

    def _watchdog(self, proc, output_prefix, n_runs, per_run_limit, startup_grace, t0):
        """Kills the process group if any single run overruns its budget.

        Run i is 'done' once its {prefix}{i}.json report appears. Run 0 is
        allowed startup_grace + per_run_limit (process startup and graph loading
        counted once); each later run is allowed per_run_limit from the moment
        the previous run finished. We do not trust the solver to stop itself: a
        run stuck in a C extension (e.g. Gurobi building an ILP, where a Python
        SIGALRM cannot be delivered) or a native binary ignoring its budget is
        SIGKILLed here. Reports already written by earlier runs survive.
        """
        next_run = 0
        deadline = t0 + startup_grace + per_run_limit
        while not self._stop.is_set() and next_run < n_runs:
            if Path(f"{output_prefix}{next_run}.json").exists():
                next_run += 1
                deadline = time.monotonic() + per_run_limit
                continue
            if time.monotonic() > deadline:
                self.watchdog_killed_run = next_run
                self._kill_solver(proc)
                return
            self._stop.wait(0.5)

    # -- execution ----------------------------------------------------------

    def run(self, argv, cwd, env, timeout, allow_rlimit,
            output_prefix=None, n_runs=1, per_run_limit=None, startup_grace=0.0):
        """Executes argv, returning (exit_code, stdout, stderr, wall_seconds)."""
        use_cgroup = self.cgroups_available()
        t0 = time.monotonic()

        if use_cgroup:
            unit = f"cb-{os.getpid()}-{int(t0 * 1000) % 1000000}"
            limit = str(int(self.memory_limit_gb * 1024**3))
            fd, self._peak_file = tempfile.mkstemp(prefix="cb-peak-")
            os.close(fd)
            env = dict(env)
            env["CB_PEAK_FILE"] = self._peak_file
            wrapper = [
                "systemd-run",
                "--user",
                "--scope",
                "--quiet",
                "--collect",
                f"--unit={unit}",
                "-p",
                f"MemoryMax={limit}",
                "-p",
                "MemorySwapMax=0",
                "--",
                "sh",
                "-c",
                self.PEAK_WRAPPER,
                "_",
            ]
            self.method = "cgroup"
        else:
            wrapper = []
            unit = None
            self.method = "proc-rss"

        preexec = None
        if not use_cgroup and allow_rlimit:
            # Only safe without a GPU: CUDA reserves a very large virtual
            # address space and would fail to initialise under RLIMIT_AS.
            import resource

            limit_bytes = int(self.memory_limit_gb * 1024**3)

            def preexec():
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))

        proc = subprocess.Popen(
            wrapper + argv,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=preexec,
            start_new_session=True,
            text=True,
        )

        if use_cgroup:
            # The scope appears shortly after systemd-run starts.
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline and self._cgroup is None:
                self._cgroup = self._find_cgroup(unit)
                if self._cgroup is None:
                    time.sleep(0.05)
            sampler = threading.Thread(target=self._sample_cgroup, args=(t0,), daemon=True)
        else:
            sampler = threading.Thread(
                target=self._sample_proc, args=(proc.pid, t0), daemon=True
            )
        sampler.start()

        watchdog = None
        if per_run_limit is not None and output_prefix is not None:
            watchdog = threading.Thread(
                target=self._watchdog,
                args=(proc, output_prefix, n_runs, per_run_limit, startup_grace, t0),
                daemon=True,
            )
            watchdog.start()

        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            self._kill_solver(proc)
            stdout, stderr = proc.communicate()
        except KeyboardInterrupt:
            # ctrl-c (or SIGTERM, which main() re-raises as KeyboardInterrupt).
            # The solver runs in its own session, so the signal never reached it --
            # without this it would keep running orphaned after the harness dies.
            # Kill the whole tree, reap, then re-raise so main() exits.
            self._stop.set()
            self._kill_solver(proc)
            proc.communicate()
            raise

        wall = time.monotonic() - t0
        self._stop.set()
        sampler.join(timeout=2.0)
        if watchdog:
            watchdog.join(timeout=2.0)

        # Authoritative value, written from inside the cgroup by the wrapper.
        if self._peak_file:
            try:
                text = Path(self._peak_file).read_text().strip()
                if text:
                    self.peak_bytes = int(text)
            except (OSError, ValueError):
                pass
            finally:
                Path(self._peak_file).unlink(missing_ok=True)

        if self.peak_bytes is None and self.samples:
            self.peak_bytes = max(v for _, v in self.samples)

        # A SIGKILL exit under a memory limit is the signature of the cgroup
        # OOM killer; the scope is gone by now so memory.events is unreadable.
        # A watchdog kill is also a SIGKILL, so exclude it here.
        if (
            use_cgroup
            and proc.returncode in (-9, 137)
            and not timed_out
            and self.watchdog_killed_run is None
        ):
            self.oom_killed = True

        return proc.returncode, stdout, stderr, wall, timed_out


# --------------------------------------------------------------------------
# parameter resolution
# --------------------------------------------------------------------------


def coerce(value, spec):
    kind = spec.get("type", "str")
    if isinstance(value, str):
        if kind == "int":
            return int(value)
        if kind == "float":
            return float(value)
        if kind == "bool":
            return value.lower() in ("1", "true", "yes", "on")
    return value


def resolve_params(solver, overlay_path, overrides):
    """defaults from solver.json, then the overlay file, then --set flags."""
    specs = solver.get("params", {})
    params = {name: spec["default"] for name, spec in specs.items()}
    source = {name: "default" for name in params}

    if overlay_path:
        with open(overlay_path) as f:
            overlay = json.load(f)
        for name, value in overlay.items():
            if name not in specs:
                raise SystemExit(
                    f"{overlay_path}: unknown parameter '{name}' for solver "
                    f"'{solver['name']}'. Known: {sorted(specs)}"
                )
            params[name] = coerce(value, specs[name])
            source[name] = "overlay"

    for item in overrides:
        if "=" not in item:
            raise SystemExit(f"--set expects key=value, got '{item}'")
        name, _, value = item.partition("=")
        if name not in specs:
            raise SystemExit(
                f"--set: unknown parameter '{name}' for solver '{solver['name']}'. "
                f"Known: {sorted(specs)}"
            )
        params[name] = coerce(value, specs[name])
        source[name] = "override"

    return params, source


def config_hash(params):
    import hashlib

    blob = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def csr_num_nodes(path):
    """Reads n from a binary CSR header (8-byte magic, then int64 n)."""
    with open(path, "rb") as f:
        head = f.read(16)
    if not head.startswith(b"CBCSRv1"):
        raise SystemExit(f"{path} is not a binary CSR file; run CONVERT first")
    return int.from_bytes(head[8:16], "little", signed=True)


def num_labels(path):
    """Number of distinct labels in a labels file (the true k)."""
    with open(path) as f:
        return len({line.strip() for line in f if line.strip()})


def resolve_clusters(solver, args):
    """Resolves --clusters, deriving it from cluster_policy when 'auto'.

    exact:         true k on labelled graphs, ceil(sqrt(n)) on DIMACS.
    overprovision: max(16, true k) on labelled graphs, ceil(sqrt(n)) on DIMACS.
    An explicit integer overrides the policy; solvers that determine their own
    count (clusters capability false) get None.
    """
    if not solver.get("capabilities", {}).get("clusters"):
        return None, None
    if str(args.clusters) != "auto":
        k = int(args.clusters)
        if k < 1:
            raise SystemExit(f"solver '{solver['name']}' requires --clusters >= 1")
        return k, "explicit"
    policy = solver.get("cluster_policy", "exact")
    true_k = num_labels(args.labels) if args.labels else None
    if true_k:
        k = true_k if policy == "exact" else max(16, true_k)
    else:
        k = max(1, math.ceil(math.sqrt(csr_num_nodes(args.graph))))
    return k, f"auto:{policy}"


def add_flag(argv, flag, value):
    """Supports both '--flag=' and '--flag' spellings."""
    if flag.endswith("="):
        argv.append(f"{flag}{value}")
    else:
        argv.extend([flag, str(value)])


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def build_command(solver, args, params, output_prefix, solver_dir):
    io = solver.get("io", {})
    caps = solver.get("capabilities", {})

    argv = shlex.split(solver["entry"])

    add_flag(argv, io["graph"], args.graph)
    add_flag(argv, io["output"], output_prefix)

    if "runs" in io:
        add_flag(argv, io["runs"], args.runs)
    if "timeout" in io:
        add_flag(argv, io["timeout"], args.time)
    if "threads" in io and caps.get("threads"):
        add_flag(argv, io["threads"], args.threads)
    if "clusters" in io and caps.get("clusters"):
        add_flag(argv, io["clusters"], args.clusters)
    if "memory" in io:
        add_flag(argv, io["memory"], args.memory)
    if "seed" in io:
        add_flag(argv, io["seed"], args.seed)
    if "device" in io and caps.get("gpu"):
        add_flag(argv, io["device"], args.device)
    if "features" in io and caps.get("features") and args.features:
        add_flag(argv, io["features"], args.features)

    for name, value in params.items():
        spec = solver["params"][name]
        if spec.get("type") == "bool":
            if value and "flag" in spec:
                argv.append(spec["flag"].rstrip("="))
            continue
        add_flag(argv, spec["flag"], value)

    return argv


def resolve_solver(spec):
    """Accepts a solver name, a solver directory, or a path to solver.json."""
    candidate = Path(spec)
    if candidate.is_file():
        return candidate.resolve()
    if (candidate / "solver.json").is_file():
        return (candidate / "solver.json").resolve()

    matches = sorted(REPO_ROOT.glob(f"external/*/solver.json"))
    named = [m for m in matches if json.loads(m.read_text()).get("name") == spec]
    if len(named) == 1:
        return named[0]
    if len(named) > 1:
        raise SystemExit(
            f"solver name '{spec}' is ambiguous: {[str(m) for m in named]}"
        )

    available = sorted(json.loads(m.read_text()).get("name", "?") for m in matches)
    raise SystemExit(
        f"unknown solver '{spec}'. Migrated solvers: {', '.join(available) or '(none)'}"
    )


def main():
    p = argparse.ArgumentParser(
        description="Unified solver harness", allow_abbrev=False
    )
    p.add_argument(
        "--solver",
        required=True,
        help="solver name (e.g. louvain), solver directory, or path to solver.json",
    )
    p.add_argument("--graph", required=True, help="graph file, METIS or binary CSR")
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, required=True, help="per-run limit in seconds")
    p.add_argument("--memory", type=float, required=True, help="limit in GB")
    p.add_argument(
        "--grace",
        type=float,
        default=30.0,
        help="per-run hard-kill grace on top of --time; the harness SIGKILLs the "
        "solver once the whole invocation exceeds runs*(time+max(grace,0.25*time)) "
        "+ startup-grace, so a solver that ignores its own limit is still stopped",
    )
    p.add_argument(
        "--startup-grace",
        type=float,
        default=120.0,
        help="one-off allowance (s) for process startup and graph loading before "
        "the hard kill; raise it for very large graphs that are slow to load",
    )
    p.add_argument("--threads", type=int, default=1)
    p.add_argument(
        "--clusters",
        default="auto",
        help="target cluster count, or 'auto' to derive from the solver's cluster_policy",
    )
    p.add_argument("--features", default=None)
    p.add_argument("--labels", default=None)
    p.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    p.add_argument(
        "--seed",
        type=int,
        default=0,
        help="base seed; run i uses seed + i, so repeated runs are reproducible",
    )
    p.add_argument("--params", default=None, help="overlay json of tuned parameters")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--protocol", default="default", help="label recorded in the output")
    p.add_argument("--out", default=None, help="JSONL output file, default stdout")
    p.add_argument("--workdir", default=None, help="scratch dir for solver output")
    p.add_argument("--keep", action="store_true", help="keep intermediate cluster files")
    p.add_argument(
        "--trace-memory",
        action="store_true",
        help="record the full memory time series (debugging; large output)",
    )
    args = p.parse_args()

    solver_path = resolve_solver(args.solver)
    with open(solver_path) as f:
        solver = json.load(f)
    solver_dir = solver_path.parent

    args.graph = str(Path(args.graph).resolve())
    if args.features:
        args.features = str(Path(args.features).resolve())

    # Labels default to a sibling .labels file, as before.
    if args.labels is None:
        guess = Path(args.graph)
        for suffix in (".csr", ".graph"):
            if guess.name.endswith(suffix):
                candidate = Path(str(guess)[: -len(suffix)] + ".labels")
                if candidate.exists():
                    args.labels = str(candidate)
                break
    elif args.labels:
        args.labels = str(Path(args.labels).resolve())

    # Resolve the cluster count now that the graph and labels are known, so
    # 'auto' can consult cluster_policy, the graph size, and the true k.
    args.clusters, cluster_mode = resolve_clusters(solver, args)

    params, source = resolve_params(solver, args.params, args.set)
    chash = config_hash(params)

    instance = Path(args.graph).name
    for suffix in (".csr", ".graph"):
        if instance.endswith(suffix):
            instance = instance[: -len(suffix)]
            break

    workdir = Path(args.workdir).resolve() if args.workdir else Path.cwd() / ".cb_work"
    workdir.mkdir(parents=True, exist_ok=True)
    output_prefix = str(workdir / f"{instance}_{solver['name']}_{chash}_")

    cwd = solver_dir / solver.get("cwd", ".")
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(args.threads)
    env["MKL_NUM_THREADS"] = str(args.threads)
    env["PYTHONUNBUFFERED"] = "1"
    if solver.get("venv"):
        venv = (solver_dir / solver["venv"]).resolve()
        env["VIRTUAL_ENV"] = str(venv)
        env["PATH"] = f"{venv / 'bin'}:{env['PATH']}"
        env.pop("PYTHONHOME", None)
    if args.device == "cpu":
        env["CUDA_VISIBLE_DEVICES"] = ""

    argv = build_command(solver, args, params, output_prefix, solver_dir)

    caps = solver.get("capabilities", {})
    gpu = args.device == "cuda" and caps.get("gpu", False)

    # The solver is asked to honour the per-run limit itself, but we do not
    # trust it to: a run stuck in a C extension (e.g. Gurobi building an ILP)
    # never gets to act on a Python SIGALRM, and a native binary may ignore its
    # budget. The monitor's watchdog enforces the limit per run -- each run gets
    # its --time plus a grace margin for a brief overrun -- and SIGKILLs the
    # process group if a single run exceeds it; runs that already wrote a report
    # survive. per_run_limit is what each run is allowed; outer_timeout is only a
    # loose final backstop on the whole invocation in case the watchdog is
    # somehow bypassed.
    per_run_limit = args.time + max(args.grace, 0.25 * args.time)
    outer_timeout = args.startup_grace + args.runs * per_run_limit + 60

    # Clear any stale reports for this prefix so the watchdog, which treats a
    # report file as "run finished", is not fooled by output from a prior run of
    # the same config.
    for i in range(args.runs):
        Path(f"{output_prefix}{i}.json").unlink(missing_ok=True)
        Path(f"{output_prefix}{i}.txt").unlink(missing_ok=True)

    monitor = MemoryMonitor(args.memory, trace=args.trace_memory)
    code, stdout, stderr, wall, timed_out = monitor.run(
        argv, cwd=str(cwd), env=env, timeout=outer_timeout, allow_rlimit=not gpu,
        output_prefix=output_prefix, n_runs=args.runs,
        per_run_limit=per_run_limit, startup_grace=args.startup_grace,
    )

    out = open(args.out, "a") if args.out else sys.stdout

    common = {
        "solver": solver["name"],
        "class": solver.get("class"),
        "protocol": args.protocol,
        "instance": instance,
        "config": params,
        "config_source": source,
        "config_hash": chash,
        "device": args.device,
        "threads": args.threads,
        "seed": args.seed,
        "requested": {
            "runs": args.runs,
            "time_limit": args.time,
            "memory_limit_gb": args.memory,
            "clusters": args.clusters,
            "cluster_mode": cluster_mode,
        },
        "memory": {
            "peak_bytes": monitor.peak_bytes,
            "peak_mb": round(monitor.peak_bytes / 1e6, 1) if monitor.peak_bytes else None,
            "method": monitor.method,
            "oom_killed": monitor.oom_killed,
            # Full time series only when explicitly requested (--trace-memory).
            **({"samples": monitor.samples} if monitor.trace else {}),
        },
        "process": {
            "exit_code": code,
            "wall_seconds": round(wall, 4),
            "outer_timeout": timed_out,
            "per_run_limit_seconds": round(per_run_limit, 1),
            "watchdog_killed_run": monitor.watchdog_killed_run,
        },
        "env": {
            "host": os.uname().nodename,
            "git_commit": git_commit(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    }

    if stderr.strip():
        common["stderr_tail"] = stderr.strip()[-2000:]

    emitted = 0
    for i in range(args.runs):
        record = dict(common)
        record["run"] = i

        report_path = Path(f"{output_prefix}{i}.json")
        clustering_path = Path(f"{output_prefix}{i}.txt")

        if report_path.exists():
            with open(report_path) as f:
                record["solver_report"] = json.load(f)

        if monitor.oom_killed:
            record["status"] = "mle"
        elif clustering_path.exists():
            record["status"] = "ok"
        elif record.get("solver_report", {}).get("status") == "tle":
            record["status"] = "tle"
        elif monitor.watchdog_killed_run is not None and i >= monitor.watchdog_killed_run:
            # This run (and any after it) never finished before the hard kill.
            record["status"] = "tle"
        elif timed_out:
            record["status"] = "tle"
        else:
            record["status"] = "error"

        if clustering_path.exists():
            eval_argv = [str(EVAL_BIN), args.graph, str(clustering_path)]
            if args.labels:
                eval_argv.append(args.labels)
            eval_argv.append("--json")
            r = subprocess.run(eval_argv, capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                record["quality"] = json.loads(r.stdout)
            else:
                record["status"] = "error"
                record["eval_stderr"] = r.stderr.strip()[-1000:]

        out.write(json.dumps(record) + "\n")
        emitted += 1

        if not args.keep:
            clustering_path.unlink(missing_ok=True)
            report_path.unlink(missing_ok=True)

    out.flush()
    if args.out:
        out.close()

    return 0 if emitted == args.runs else 1


def git_commit():
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        )
        return r.stdout.strip() or None
    except OSError:
        return None


def _sigterm(_signum, _frame):
    # Turn SIGTERM into the same path as ctrl-c so `kill <harness>` also tears
    # down the solver's process group instead of orphaning it.
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _sigterm)
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # The solver has already been killed in MemoryMonitor.run; exit with the
        # conventional 128+SIGINT code, no traceback.
        sys.exit(130)
