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
    p.add_argument("--hidden", type=int, default=64)
    p.add_argument("--learning-rate", type=float, default=0.001)
    p.add_argument("--clustertemp", type=float, default=30.0)
    p.add_argument("--weight-decay", type=float, default=0.2)
    # Loss coefficients from the paper's Eq. 9 (alpha on the DGI/graph MI term,
    # beta on the community MI term). The paper uses alpha=2, beta=5 and Figs 6/7
    # sweep them. Our earlier code copied the repo's commented-out line, which put
    # the large weight on the DGI term instead of community; this restores Eq. 9.
    p.add_argument("--graph-weight", type=float, default=2.0)
    p.add_argument("--community-weight", type=float, default=5.0)
    # Protocol B improvement: compute the modularity term from the sparse
    # adjacency instead of the authors' dense n x n modularity matrix. The two
    # are numerically equivalent (verified), but the dense form is O(n^2) memory
    # and compute and MLEs on large graphs. Off by default so Protocol A stays
    # faithful to the reference code.
    p.add_argument("--sparse-modularity", action="store_true")


def make_modularity_matrix(adj, torch):
    """B = A - dd^T / 2m, over the off-diagonal adjacency (authors' setup)."""
    # Build the off-diagonal mask on adj's own device; otherwise a GPU adj hits a
    # cuda/cpu mismatch (the authors only ever ran this on CPU).
    adj = adj * (torch.ones(adj.shape[0], adj.shape[0], device=adj.device)
                 - torch.eye(adj.shape[0], device=adj.device))
    degrees = adj.sum(dim=0).unsqueeze(1)
    return adj - degrees @ degrees.t() / adj.sum()


def sparse_modularity(r, adj_sp, degree, two_m):
    """DGI.modularity without forming B: (1/2m)(trace(r^T A_nodiag r) - ||d^T r||^2/2m)."""
    import torch

    ar = torch.sparse.mm(adj_sp, r)
    term1 = (r * ar).sum()
    dr = degree @ r
    return (term1 - (dr * dr).sum() / two_m) / two_m


def main():
    ctx = mlrunner.setup("CommDGI graph clustering", add_arguments)
    device = ctx.use_torch()

    import torch
    from model import Encoder, Summarizer, cluster_net, corruption
    from DGI import DeepGraphInfomax

    args = ctx.args
    N = ctx.graph.n

    # The modularity term is CommDGI's only O(n^2) piece. Protocol A builds the
    # authors' dense adjacency and modularity matrix; Protocol B keeps it sparse.
    a_sparse = ctx.graph.to_scipy_csr()
    adj_all = test_object = None
    adj_sp = degree = two_m = None
    if args.sparse_modularity:
        a_nodiag = a_sparse.astype(np.float32)
        a_nodiag.setdiag(0)
        a_nodiag.eliminate_zeros()
        coo = a_nodiag.tocoo()
        adj_sp = torch.sparse_coo_tensor(
            np.vstack([coo.row, coo.col]), coo.data, size=(N, N)
        ).coalesce().to(device)
        degree = torch.tensor(
            np.asarray(a_nodiag.sum(axis=1)).ravel(), dtype=torch.float32
        ).to(device)
        two_m = degree.sum()
    else:
        adj_all = torch.from_numpy(a_sparse.toarray().astype(np.float32)).to(device)
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
            if hasattr(model, "init") and isinstance(model.init, torch.Tensor):
                model.init = model.init.to(device)
            optimizer = torch.optim.Adam(
                model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
            )

            for _ in run.epochs(args.train_iters):
                model.train()
                optimizer.zero_grad()
                pos_z, neg_z, summary, mu, r, dist = model(features, edge_index)
                dgi_loss = model.loss(pos_z, neg_z, summary)
                if args.sparse_modularity:
                    modularity_loss = sparse_modularity(r, adj_sp, degree, two_m)
                else:
                    modularity_loss = model.modularity(
                        mu, r, pos_z, dist, adj_all, test_object, model_args
                    )
                comm_loss = model.comm_loss(pos_z, mu)
                loss = (
                    -modularity_loss
                    + args.graph_weight * dgi_loss
                    + args.community_weight * comm_loss
                )
                loss.backward()
                optimizer.step()

            model.eval()
            with torch.no_grad():
                _, _, _, _, r, _ = model(features, edge_index)
                clusters = r.argmax(dim=1).cpu().numpy()
            run.result(clusters)


if __name__ == "__main__":
    main()
