"""Shared scaffolding for learning-based clustering solvers.

This is a library of services, not a framework. It deliberately does not own
the training loop: the solvers span TensorFlow and PyTorch and their model APIs
are incompatible, so forcing them into a common loop would mean rewriting the
authors' code, which is exactly the provenance we are trying to preserve.

What is shared here is everything that is not the method: argument parsing,
graph and feature loading, synthetic features for featureless graphs, seeding,
device selection with verification, the stopping policy, and report writing.

A driver looks like this:

    ctx = mlrunner.setup("DMoN")
    device = ctx.use_torch()               # or ctx.use_tensorflow()

    for run in ctx.runs():
        with run:
            model = build_model(...)       # authors' code, untouched
            for epoch in run.epochs(ctx.args.epochs):
                train_step(model)          # authors' code, untouched
            run.result(clusters)

Where the training loop lives inside an author function instead, patch that
function to accept a `should_stop` callback and pass `run.should_stop`. The
stopping policy then stays here for every solver.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import features as featurelib  # noqa: E402
import graphio  # noqa: E402


class DeviceUnavailable(RuntimeError):
    """Raised when cuda was requested but the framework cannot see a GPU.

    This must be fatal. A run that silently falls back to CPU would be recorded
    as a GPU result, which would quietly corrupt the comparison it exists to
    support.
    """


class RunContext:
    """One run of a solver: seeding, stopping policy, and its report."""

    def __init__(self, ctx, index):
        self.ctx = ctx
        self.index = index
        self.seed = ctx.args.seed + index
        self.status = "ok"
        self.error = None
        self.iterations_done = 0
        self.iterations_requested = None
        self.extra = {}
        self._clusters = None
        self._start = None
        self._elapsed = None
        self._deadline = None

    # -- lifecycle ----------------------------------------------------------

    def __enter__(self):
        self.ctx._seed_everything(self.seed)
        self._start = time.perf_counter()
        limit = self.ctx.args.time
        self._deadline = self._start + limit if limit and limit > 0 else None
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._elapsed is None:
            self._elapsed = time.perf_counter() - self._start

        if exc_type is not None:
            self.status = "error"
            self.error = f"{exc_type.__name__}: {exc}"

        self._write_report()
        # Report the failure and continue to the next run rather than aborting
        # the whole invocation; the harness reads status per run.
        return exc_type is not None

    # -- stopping policy ----------------------------------------------------

    def should_stop(self):
        """True once the per-run time limit has passed.

        Pass this as a callback into author-owned training loops.
        """
        return self._deadline is not None and time.perf_counter() >= self._deadline

    def epochs(self, n_epochs):
        """Yields epoch indices, stopping early on the time limit."""
        self.iterations_requested = n_epochs
        for epoch in range(n_epochs):
            if self.should_stop():
                self.status = "tle"
                break
            yield epoch
            self.iterations_done = epoch + 1

    def remaining(self):
        """Seconds left in the budget, or None when unbounded."""
        if self._deadline is None:
            return None
        return max(0.0, self._deadline - time.perf_counter())

    # -- results ------------------------------------------------------------

    def result(self, clusters, **extra):
        """Records the clustering for this run."""
        clusters = np.asarray(clusters).reshape(-1)
        if clusters.size != self.ctx.graph.n:
            raise ValueError(
                f"clustering has {clusters.size} entries, expected {self.ctx.graph.n}"
            )
        self._clusters = clusters
        self._elapsed = time.perf_counter() - self._start
        self.extra.update(extra)

    def _write_report(self):
        prefix = self.ctx.args.output_prefix
        if self._clusters is not None:
            graphio.write_clustering(f"{prefix}{self.index}.txt", self._clusters)

        report = {
            "run": self.index,
            "seed": self.seed,
            "status": self.status,
            "solve_seconds": round(self._elapsed, 6) if self._elapsed else 0.0,
            "parse_seconds": round(self.ctx.parse_seconds, 6),
            "iterations": {
                "done": self.iterations_done,
                "requested": self.iterations_requested,
            },
            "device_requested": self.ctx.args.device,
            "device_actual": self.ctx.device_actual,
            "features": (
                None
                if self.ctx.features is None
                else {
                    "kind": self.ctx.feature_kind,
                    "dim": int(self.ctx.features.shape[1]),
                    "synthetic": self.ctx.features_synthetic,
                }
            ),
        }
        if self.error:
            report["error"] = self.error
        report.update(self.extra)

        with open(f"{prefix}{self.index}.json", "w") as f:
            json.dump(report, f)


class Context:
    """Shared state for an invocation: the graph, features, and device."""

    def __init__(self, args, needs_features=True):
        self.args = args
        self.device_actual = None
        self._seed_hooks = []

        t0 = time.perf_counter()
        self.graph = graphio.load_csr(args.graph)

        if not needs_features:
            # Structure-only methods (e.g. GNNS optimises modularity directly on
            # the graph). No representation is built, so none is recorded.
            self.features = None
            self.feature_kind = None
            self.features_synthetic = False
        elif args.features:
            self.features = np.asarray(
                graphio.load_features(args.features, self.graph.n), dtype=np.float32
            )
            self.feature_kind = "provided"
            self.features_synthetic = False
        else:
            # Featureless instance: synthesise a representation. This is a
            # methodological choice, so it is recorded in every run's report.
            self.features = featurelib.build(
                self.graph,
                kind=args.feature_kind,
                seed=args.seed,
                rni_dim=args.rni_dim,
            )
            self.feature_kind = args.feature_kind
            self.features_synthetic = True

        self.parse_seconds = time.perf_counter() - t0

    # -- framework binding --------------------------------------------------

    def use_torch(self):
        """Selects and verifies the device, seeds torch, returns a torch.device."""
        import torch

        if self.args.device == "cuda":
            if not torch.cuda.is_available():
                raise DeviceUnavailable(
                    "--device cuda requested but torch.cuda.is_available() is False. "
                    "Refusing to fall back to CPU silently."
                )
            device = torch.device("cuda")
            self.device_actual = f"cuda:{torch.cuda.current_device()}"
        else:
            device = torch.device("cpu")
            self.device_actual = "cpu"

        def seed_torch(seed):
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)

        self._seed_hooks.append(seed_torch)
        if self.args.threads:
            torch.set_num_threads(self.args.threads)
        return device

    def use_tensorflow(self):
        """Selects and verifies the device and seeds TensorFlow."""
        import tensorflow as tf

        gpus = tf.config.list_physical_devices("GPU")
        if self.args.device == "cuda":
            if not gpus:
                raise DeviceUnavailable(
                    "--device cuda requested but TensorFlow sees no GPU. "
                    "Refusing to fall back to CPU silently. "
                    "Is tensorflow installed with the [and-cuda] extra?"
                )
            self.device_actual = gpus[0].name
        else:
            tf.config.set_visible_devices([], "GPU")
            self.device_actual = "cpu"

        if self.args.threads:
            tf.config.threading.set_intra_op_parallelism_threads(self.args.threads)
            tf.config.threading.set_inter_op_parallelism_threads(self.args.threads)

        self._seed_hooks.append(lambda seed: tf.random.set_seed(seed))
        return self.device_actual

    # -- seeding ------------------------------------------------------------

    def _seed_everything(self, seed):
        import random

        random.seed(seed)
        np.random.seed(seed % (2**32))
        for hook in self._seed_hooks:
            hook(seed)

    # -- runs ---------------------------------------------------------------

    def runs(self):
        for index in range(self.args.runs):
            yield RunContext(self, index)


def build_parser(description, add_arguments=None):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--graph", required=True, help="binary CSR graph file")
    p.add_argument("--features", default=None, help="feature file, if the instance has one")
    p.add_argument("--output-prefix", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--time", type=float, default=0.0, help="per-run limit, 0 disables")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--clusters", type=int, default=16)
    p.add_argument("--threads", type=int, default=0)
    p.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    p.add_argument(
        "--feature-kind",
        default="ldp+rni",
        choices=featurelib.KINDS,
        help="representation used when the instance has no node features",
    )
    p.add_argument("--rni-dim", type=int, default=featurelib.DEFAULT_RNI_DIM)
    if add_arguments:
        add_arguments(p)
    return p


def setup(description, add_arguments=None, argv=None, needs_features=True):
    """Parses arguments and loads the graph and, unless disabled, features."""
    args = build_parser(description, add_arguments).parse_args(argv)
    return Context(args, needs_features=needs_features)
