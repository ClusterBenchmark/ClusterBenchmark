"""GNNS clustering driver on the shared ML harness.

GNNS optimises modularity directly on the graph, so it is structure-only: no
node features are built (mlrunner.setup(needs_features=False)). The algorithm is
the authors' code in gnns.py, hand-extracted from their notebook (see that
file's header for the pinned provenance); this driver only loads the graph,
sets up the engine, runs the sampler, and writes the report through mlrunner.

The old gnns.py carried its own METIS reader and a main() with a ulimit/time
shim; both are replaced here.
"""

import sys
from pathlib import Path

# This driver lives at external/gnns/run_gnns.py (not inside a cloned subdir like
# the other solvers), so the repo root is two levels up.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    p.add_argument("--num-random-configs", type=int, default=100)
    p.add_argument("--fraction-to-keep", type=float, default=1.0 / 3.0)
    p.add_argument(
        "--iterations-per-stage",
        default="auto",
        help="GNNS iterations per stage; 'auto' derives the schedule from the config count (Algorithm 1)",
    )
    p.add_argument("--max-total-tensor-size", type=int, default=100_000_000)


def main():
    ctx = mlrunner.setup("GNNS graph clustering", add_arguments, needs_features=False)
    ctx.use_torch()  # device selection + verification + torch seeding

    import torch

    import gnns

    args = ctx.args
    # GNNS works in float64 and reads its configuration from module globals.
    torch.set_default_dtype(torch.float64)
    gnns.hypers = {
        "strip_diagonal": True,
        "normalize_modularity": False,
        "normalize_each_step": True,
        "use_sparse": True,
        "max_batch_size": 1000,
        "max_total_tensor_size": args.max_total_tensor_size,
    }
    gnns.eng = gnns.Engine("torch")

    G = nx.from_scipy_sparse_array(ctx.graph.to_scipy_csr())
    max_communities = args.clusters
    if str(args.iterations_per_stage) == "auto":
        # Algorithm 1: append a 100-iteration stage once S exceeds 1000.
        iterations_per_stage = [10, 10, 30, 100] if args.num_random_configs > 1000 else [10, 10, 30]
    else:
        iterations_per_stage = [int(x) for x in str(args.iterations_per_stage).split(",") if x]

    for run in ctx.runs():
        with run:
            gnns.set_all_random_seeds(run.seed)
            best_communities, _, _, best_mod, _, iterations = gnns.runGNNSSeries(
                G,
                max_num_communities=max_communities,
                iterations_per_stage=iterations_per_stage,
                num_random_configs=args.num_random_configs,
                fraction_to_keep=args.fraction_to_keep,
                manual_gc=(len(G) > 1000),
                verbose=0,
                timeout=run.remaining(),
            )
            run.iterations_done = iterations

            if best_communities is None:
                # The budget elapsed before any configuration finished a stage.
                run.status = "tle"
                continue

            partition = best_communities.argmax(axis=1)
            if hasattr(partition, "detach"):
                partition = partition.detach().cpu().numpy()
            run.result(np.asarray(partition), modularity=float(best_mod))


if __name__ == "__main__":
    main()
