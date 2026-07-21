"""MAGI-SAGE clustering driver on the shared ML harness (minibatch variant).

This is MAGI's scalable path (train_sage.py): the GNN is trained on minibatches
sampled by NeighborSampler rather than the full graph, so it does not build the
dense N x N similarity that the GCN variant (external/magi) does and can run on
graphs too large for that variant. The method is the authors' code, imported
unchanged from the cloned upstream (Encoder/Model, NeighborSampler, get_mask,
setup_seed); this driver assembles it and runs training, while graph and feature
loading, seeding, the per-run time limit, and report writing come from mlrunner.
No patch is applied.

The readout is KMeans over the learned embedding (seeded, unlike the authors').
NeighborSampler shuffles minibatches, so exact per-seed reproducibility holds
only with --num-workers 0 (the default); raising it trades that for throughput.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--hidden-channels", default="512,256", help="per-layer encoder widths")
    p.add_argument("--size", default="10,10", help="per-layer neighbour sample sizes")
    p.add_argument("--batchsize", type=int, default=2048)
    p.add_argument("--learning-rate", type=float, default=0.01)
    p.add_argument("--weight-decay", type=float, default=0.0)
    p.add_argument("--tau", type=float, default=0.5)
    p.add_argument("--wt", type=int, default=20, help="number of random walks")
    p.add_argument("--wl", type=int, default=4, help="depth of random walks")
    p.add_argument("--dropout", type=float, default=0.0)
    p.add_argument("--ns", type=float, default=0.5)
    p.add_argument("--num-workers", type=int, default=0, help="DataLoader workers")


def main():
    ctx = mlrunner.setup("MAGI-SAGE graph clustering", add_arguments, needs_features=True)
    device = ctx.use_torch()

    import torch
    import torch.nn.functional as F
    from torch_geometric.utils import add_remaining_self_loops, to_undirected
    from torch_sparse import SparseTensor
    from sklearn.cluster import KMeans

    from magi.model import Encoder, Model
    from magi.neighbor_sampler import NeighborSampler
    from magi.utils import get_mask, setup_seed

    args = ctx.args
    N = ctx.graph.n

    src = np.asarray(ctx.graph.sources(), dtype=np.int64)
    dst = np.asarray(ctx.graph.E, dtype=np.int64)
    edge_index = torch.from_numpy(np.vstack([src, dst]))
    edge_index = to_undirected(add_remaining_self_loops(edge_index)[0])

    adj = SparseTensor(row=edge_index[0], col=edge_index[1], sparse_sizes=(N, N))
    adj.fill_value_(1.0)

    hidden = list(map(int, str(args.hidden_channels).split(",")))
    size = list(map(int, str(args.size).split(",")))
    if len(hidden) != len(size):
        raise ValueError(
            f"--hidden-channels ({hidden}) and --size ({size}) must have equal length"
        )

    # Features stay on CPU and are moved per minibatch, so the whole feature
    # matrix never has to fit on the GPU (the point of the SAGE variant).
    x = torch.from_numpy(np.ascontiguousarray(ctx.features, dtype=np.float32))
    num_features = x.shape[1]

    for run in ctx.runs():
        with run:
            setup_seed(run.seed)
            train_loader = NeighborSampler(
                edge_index, adj, is_train=True, node_idx=None,
                wt=args.wt, wl=args.wl, sizes=size, batch_size=args.batchsize,
                shuffle=True, drop_last=True, num_workers=args.num_workers,
            )
            test_loader = NeighborSampler(
                edge_index, adj, is_train=False, node_idx=None, sizes=size,
                batch_size=10000, shuffle=False, drop_last=False,
                num_workers=args.num_workers,
            )

            encoder = Encoder(
                num_features, hidden_channels=hidden, dropout=args.dropout, ns=args.ns
            ).to(device)
            model = Model(
                encoder, in_channels=hidden[-1], project_hidden=None, tau=args.tau
            ).to(device)
            optimizer = torch.optim.Adam(
                model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
            )

            run.iterations_requested = args.epochs
            timed_out = False
            for epoch in range(args.epochs):
                if run.should_stop():
                    timed_out = True
                    break
                model.train()
                for (batch_size, n_id, adjs), adj_batch, batch in train_loader:
                    if run.should_stop():
                        timed_out = True
                        break
                    if len(hidden) == 1:
                        adjs = [adjs]
                    adjs = [a.to(device) for a in adjs]
                    optimizer.zero_grad()
                    out = model(x[n_id].to(device), adjs=adjs)
                    out = F.normalize(out, p=2, dim=1)
                    loss = model.loss(out, get_mask(adj_batch))
                    loss.backward()
                    optimizer.step()
                run.iterations_done = epoch + 1
                if timed_out:
                    break
            if timed_out:
                run.status = "tle"

            # Embed every node (test_loader is unshuffled and covers all nodes).
            model.eval()
            z = []
            with torch.no_grad():
                for (batch_size, n_id, adjs), _, batch in test_loader:
                    if len(hidden) == 1:
                        adjs = [adjs]
                    adjs = [a.to(device) for a in adjs]
                    out = model(x[n_id].to(device), adjs=adjs)
                    z.append(out.detach().cpu().float())
            z = F.normalize(torch.cat(z, dim=0), p=2, dim=1).numpy()

            clusters = KMeans(
                n_clusters=args.clusters, max_iter=10000, n_init=20, random_state=run.seed
            ).fit_predict(z)
            run.result(clusters)


if __name__ == "__main__":
    main()
