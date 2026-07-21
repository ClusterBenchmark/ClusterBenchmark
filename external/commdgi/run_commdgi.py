"""CommDGI clustering driver on the shared ML harness.

The method is the authors' code, imported unchanged from the cloned upstream
(see build.sh / solver.json for the pinned commit): the Encoder, Summarizer,
corruption and cluster_net from model.py, and DeepGraphInfomax from DGI.py. This
file assembles them and runs the training loop, while graph and feature loading,
seeding, the per-run time limit, and report writing come from mlrunner.

It replaces the previous run_commdgi.py, which carried its own METIS parser and
text feature loader and fell back to a dense n x n identity when no features
were given. Featureless instances now use the shared synthetic representation.

Note CommDGI's modularity objective is defined over a dense n x n modularity
matrix (DGI.modularity, and make_modularity_matrix below). That density is the
method, not an artifact, so it is preserved: CommDGI genuinely does not scale to
large graphs, which is a result to report rather than a bug to fix.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    # A fixed compute budget; the per-run time limit is what actually bounds it.
    p.add_argument("--train-iters", type=int, default=1001)
    p.add_argument("--hidden", type=int, default=512)
    p.add_argument("--learning-rate", type=float, default=0.001)
    p.add_argument("--clustertemp", type=float, default=30.0)


def make_modularity_matrix(adj, torch):
    """B = A - dd^T / 2m, over the off-diagonal adjacency (authors' setup)."""
    adj = adj * (torch.ones(adj.shape[0], adj.shape[0]) - torch.eye(adj.shape[0]))
    degrees = adj.sum(dim=0).unsqueeze(1)
    return adj - degrees @ degrees.t() / adj.sum()


def main():
    ctx = mlrunner.setup("CommDGI graph clustering", add_arguments)
    device = ctx.use_torch()

    import torch
    from model import Encoder, Summarizer, cluster_net, corruption
    from DGI import DeepGraphInfomax

    args = ctx.args

    # Dense adjacency and modularity matrix: intrinsic to CommDGI's objective.
    dense_adj = ctx.graph.to_scipy_csr().toarray().astype(np.float32)
    adj_all = torch.from_numpy(dense_adj).to(device)
    test_object = make_modularity_matrix(adj_all, torch).to(device)

    # edge_index in the form PyG wants: both directions, exactly what CSR stores.
    src = np.asarray(ctx.graph.sources(), dtype=np.int64)
    dst = np.asarray(ctx.graph.E, dtype=np.int64)
    edge_index = torch.from_numpy(np.vstack([src, dst])).to(device)

    features = torch.from_numpy(
        np.ascontiguousarray(ctx.features, dtype=np.float32)
    ).to(device)
    num_features = features.shape[1]

    # The authors' modules read only args.K and args.clustertemp off this object.
    model_args = SimpleNamespace(K=args.clusters, clustertemp=args.clustertemp)

    for run in ctx.runs():
        with run:
            model = DeepGraphInfomax(
                hidden_channels=args.hidden,
                encoder=Encoder(num_features, args.hidden),
                summary=Summarizer(),
                corruption=corruption,
                args=model_args,
                cluster=cluster_net,
            ).to(device)
            optimizer = torch.optim.Adam(
                model.parameters(), lr=args.learning_rate, weight_decay=5e-3
            )

            for _ in run.epochs(args.train_iters):
                model.train()
                optimizer.zero_grad()
                pos_z, neg_z, summary, mu, r, dist = model(features, edge_index)
                dgi_loss = model.loss(pos_z, neg_z, summary)
                modularity_loss = model.modularity(
                    mu, r, pos_z, dist, adj_all, test_object, model_args
                )
                comm_loss = model.comm_loss(pos_z, mu)
                loss = -modularity_loss + 5 * dgi_loss + comm_loss
                loss.backward()
                optimizer.step()

            model.eval()
            with torch.no_grad():
                _, _, _, _, r, _ = model(features, edge_index)
                clusters = r.argmax(dim=1).cpu().numpy()
            run.result(clusters)


if __name__ == "__main__":
    main()
