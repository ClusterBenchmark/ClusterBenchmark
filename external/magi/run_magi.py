"""MAGI clustering driver on the shared ML harness (full-graph GCN variant).

The method is the authors' code, imported unchanged from the cloned upstream
(see build.sh / solver.json for the pinned commit): the Encoder/Model
(magi/model.py) and the sampling and helper functions in magi/utils.py. This
driver assembles them and runs the training loop, while graph and feature
loading, seeding, the per-run time limit, and report writing come from mlrunner.
No patch is applied; the authors' files are left pristine.

Two method notes:
  * This is the full-graph GCN variant (train_gcn.py). Its contrastive loss is a
    dense N x N similarity, so it is O(n^2) and will MLE on large graphs. MAGI's
    scalable path is the minibatch SAGE variant (train_sage.py); that is a
    separate entry point and not migrated here.
  * The readout is KMeans over the learned embedding (the authors' clustering()
    also offers a dense-affinity spectral option, which is itself O(n^2)); this
    matches the previous integration and needs a target k, so --clusters is a
    capability.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    p.add_argument("--epochs", type=int, default=400)
    p.add_argument("--hidden", default="512", help="comma-separated GNN encoder widths")
    p.add_argument("--learning-rate", type=float, default=0.0005)
    p.add_argument("--weight-decay", type=float, default=1e-3)
    p.add_argument("--tau", type=float, default=0.3, help="contrastive temperature")
    p.add_argument("--wt", type=int, default=100, help="number of random walks")
    p.add_argument("--wl", type=int, default=2, help="depth of random walks")
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--ns", type=float, default=0.5)


def main():
    ctx = mlrunner.setup("MAGI graph clustering", add_arguments)
    device = ctx.use_torch()

    import torch
    import torch.nn.functional as F
    from torch_geometric.nn import GCNConv
    from torch_geometric.utils import add_remaining_self_loops, to_undirected
    from torch_sparse import SparseTensor
    from sklearn.cluster import KMeans

    from magi.model import Encoder, Model
    from magi.utils import get_mask, get_sim, scale, setup_seed

    args = ctx.args
    N = ctx.graph.n

    src = np.asarray(ctx.graph.sources(), dtype=np.int64)
    dst = np.asarray(ctx.graph.E, dtype=np.int64)
    edge_index = torch.from_numpy(np.vstack([src, dst]))
    edge_index = to_undirected(add_remaining_self_loops(edge_index)[0])

    adj = SparseTensor(row=edge_index[0], col=edge_index[1], sparse_sizes=(N, N))
    adj.fill_value_(1.0)

    # Random-walk similarity sampling and the loss mask (authors' preprocessing).
    # get_sim draws random walks, so seed before it or the sampled graph (shared
    # across runs) would differ between invocations.
    setup_seed(args.seed)
    batch = torch.LongTensor(list(range(N)))
    batch, adj_batch = get_sim(batch, adj, wt=args.wt, wl=args.wl)
    mask = get_mask(adj_batch)

    hidden = list(map(int, str(args.hidden).split(",")))
    x = torch.from_numpy(np.ascontiguousarray(ctx.features, dtype=np.float32)).to(device)
    edge_index = edge_index.to(device)
    num_features = x.shape[1]

    for run in ctx.runs():
        with run:
            setup_seed(run.seed)
            encoder = Encoder(
                num_features, hidden, base_model=GCNConv,
                dropout=args.dropout, ns=args.ns,
            ).to(device)
            model = Model(
                encoder, in_channels=hidden[-1], project_hidden=None, tau=args.tau
            ).to(device)
            optimizer = torch.optim.Adam(
                model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
            )

            for _ in run.epochs(args.epochs):
                model.train()
                optimizer.zero_grad()
                out = model(x, edge_index)
                out = scale(out)
                out = F.normalize(out, p=2, dim=1)
                loss = model.loss(out, mask)
                loss.backward()
                optimizer.step()

            model.eval()
            with torch.no_grad():
                out = model(x, edge_index)
                out = scale(out)
                out = F.normalize(out, p=2, dim=1).detach().cpu().numpy()
            # The authors' readout leaves KMeans unseeded (n_init=20 picks the
            # best of 20 random inits); seed it so a run is reproducible.
            clusters = KMeans(
                n_clusters=args.clusters, max_iter=10000, n_init=20, random_state=run.seed
            ).fit_predict(out)
            run.result(clusters)


if __name__ == "__main__":
    main()
