"""DGCluster clustering driver on the shared ML harness.

The method is the authors' code, imported unchanged from the cloned upstream
(see build.sh / solver.json for the pinned commit): the GNN encoder and the
modularity loss_fn in main.py. This driver assembles them, sets the module
globals loss_fn reads, and runs the training loop, while graph and feature
loading, seeding, the per-run time limit, and report writing come from mlrunner.
No patch is applied; main.py and utils.py are left pristine.

Two method notes:
  * DGCluster is sparse (message passing over edge_index, modularity loss over a
    sampled sparse adjacency), so unlike CommDGI/UCoDe it is not O(n^2).
  * It does not take a target number of clusters: Birch with a distance
    threshold decides the count, so `clusters` is not a capability and the
    threshold is the granularity knob instead.

We run DGCluster as an unsupervised structural method. Its auxiliary objective
pulls the embedding toward ground-truth label structure; that is a form of
supervision, so it is disabled here (loss_fn's aux term is overridden to a scalar
zero). This matches the previous integration's choice, made explicit in one line.
"""

import contextlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    p.add_argument("--epochs", type=int, default=300)
    p.add_argument("--learning-rate", type=float, default=1e-3)
    p.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Birch distance threshold; lower yields more clusters",
    )
    p.add_argument("--base-model", default="gcn", choices=["gcn", "gat", "gin", "sage"])
    p.add_argument("--alp", type=float, default=0.0, help="output regularisation weight")


def main():
    ctx = mlrunner.setup("DGCluster graph clustering", add_arguments)
    device = ctx.use_torch()

    import scipy.sparse
    import torch
    import torch.optim.lr_scheduler as lr_scheduler
    from sklearn.cluster import Birch
    from torch_geometric.data import Data

    import main as dg

    args = ctx.args

    # Run unsupervised: the auxiliary objective needs ground-truth labels, so
    # replace it with a scalar zero on the right device (loss_fn calls .item()
    # on the aux term, so it must be a tensor, not a Python float).
    dg.aux_objective = lambda output, s: torch.zeros((), device=device)

    src = np.asarray(ctx.graph.sources(), dtype=np.int64)
    dst = np.asarray(ctx.graph.E, dtype=np.int64)
    edge_index = torch.from_numpy(np.vstack([src, dst])).to(device)
    features = torch.from_numpy(
        np.ascontiguousarray(ctx.features, dtype=np.float32)
    ).to(device)
    data = Data(x=features, edge_index=edge_index).to(device)

    num_nodes = data.x.shape[0]
    num_edges_directed = data.edge_index.shape[1]
    sparse_adj = scipy.sparse.csr_matrix(
        (np.ones(num_edges_directed), (src, dst)), shape=(num_nodes, num_nodes)
    )
    degree = torch.tensor(sparse_adj.sum(axis=1)).squeeze().float().to(device)

    # Globals the authors' loss_fn reads from its own module.
    dg.num_nodes = num_nodes
    dg.num_edges = num_edges_directed // 2
    dg.sparse_adj = sparse_adj
    dg.degree = degree
    dg.device = device

    in_dim = data.x.shape[1]
    out_dim = 64

    for run in ctx.runs():
        with run:
            model = dg.GNN(in_dim, out_dim, base_model=args.base_model).to(device)
            optimizer = torch.optim.Adam(
                model.parameters(),
                lr=args.learning_rate,
                betas=(0.9, 0.999),
                weight_decay=0.001,
                amsgrad=True,
            )
            scheduler = lr_scheduler.LinearLR(
                optimizer, start_factor=1.0, end_factor=0.1, total_iters=args.epochs
            )
            model.train()
            # loss_fn prints every epoch; silence it so long runs do not flood
            # the captured stdout.
            with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull):
                for _ in run.epochs(args.epochs):
                    optimizer.zero_grad()
                    out = model(data)
                    loss = dg.loss_fn(out, 0.0, args.alp, -1)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1)
                    optimizer.step()
                    scheduler.step()

            model.eval()
            with torch.no_grad():
                embedding = model(data).detach().cpu().numpy()
            clusters = Birch(n_clusters=None, threshold=args.threshold).fit_predict(
                embedding
            )
            run.result(clusters)


if __name__ == "__main__":
    main()
