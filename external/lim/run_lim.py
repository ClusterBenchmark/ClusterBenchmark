"""LIM (Less-is-More) clustering driver on the shared ML harness.

The method is the authors' code, imported unchanged from the cloned upstream
(see build.sh / solver.json for the pinned commit): the Encoder, Summarizer,
corruption, cluster_net (model.py) and DeepGraphInfomax (DGI.py). This driver
reproduces the authors' setup around them -- the modularity matrix and the
"less is more" structural-community selection -- and runs the training loop,
while graph and feature loading, seeding, the per-run time limit, and report
writing come from mlrunner. The old driver mixed all that into the authors'
main.py and fell back to a dense n x n identity when no features were given;
featureless instances now use the shared synthetic representation.

Method notes:
  * LIM is O(n^2): a dense modularity matrix and a dense adjacency. It does not
    scale to large graphs, which is a result to report.
  * It takes no target k. Louvain finds structural communities, the large ones
    (size above mean + 0.5*std) are kept as cluster anchors, and their count is
    the number of clusters -- so clusters is not a capability and the Louvain
    resolution is the granularity knob instead.

The patch is a single device-correctness fix in DGI.forward (build the community
index tensors on the embedding's device) so the model can run on GPU.
"""

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    p.add_argument("--epochs", type=int, default=300)
    p.add_argument("--hidden", type=int, default=512)
    p.add_argument("--learning-rate", type=float, default=0.001)
    p.add_argument("--clustertemp", type=float, default=30.0)
    p.add_argument(
        "--resolution",
        type=float,
        default=0.3,
        help="Louvain resolution for the structural-community selection",
    )
    # Protocol B improvement: compute the modularity term from the sparse
    # adjacency instead of the authors' dense n x n modularity matrix. The two
    # are numerically equivalent (verified), but the dense form is O(n^2) memory
    # and compute and MLEs on large graphs. Off by default so Protocol A stays
    # faithful to the reference code.
    p.add_argument("--sparse-modularity", action="store_true")


def make_modularity_matrix(adj, torch):
    """B = A - dd^T / 2m over the off-diagonal adjacency (authors' setup)."""
    adj = adj * (torch.ones(adj.shape[0], adj.shape[0]) - torch.eye(adj.shape[0]))
    degrees = adj.sum(dim=0).unsqueeze(1)
    return adj - degrees @ degrees.t() / adj.sum()


def sparse_modularity(r, adj_sp, degree, two_m):
    """DGI.modularity without forming B: -(1/2m)(trace(r^T A_nodiag r) - ||d^T r||^2/2m)."""
    import torch

    ar = torch.sparse.mm(adj_sp, r)
    term1 = (r * ar).sum()
    dr = degree @ r
    return -(term1 - (dr * dr).sum() / two_m) / two_m


def main():
    ctx = mlrunner.setup("LIM graph clustering", add_arguments)
    device = ctx.use_torch()

    import networkx as nx
    import torch

    from DGI import DeepGraphInfomax
    from model import Encoder, Summarizer, cluster_net, corruption

    args = ctx.args
    N = ctx.graph.n

    # The modularity term is the only O(n^2) part of LIM. Protocol A builds the
    # authors' dense adjacency and modularity matrix; Protocol B keeps it sparse.
    a_sparse = ctx.graph.to_scipy_csr()
    adj_dense = test_object = None
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
        adj_dense = torch.from_numpy(a_sparse.toarray().astype(np.float32))
        test_object = make_modularity_matrix(adj_dense, torch).to(device)
        adj_dense = adj_dense.to(device)

    src = np.asarray(ctx.graph.sources(), dtype=np.int64)
    dst = np.asarray(ctx.graph.E, dtype=np.int64)
    edge = torch.from_numpy(np.vstack([src, dst])).to(device)

    feat = torch.from_numpy(np.ascontiguousarray(ctx.features, dtype=np.float32)).to(device)
    num_features = feat.shape[1]

    # "Less is More": keep only the large Louvain communities as cluster anchors;
    # their count is K. Seeded (123) so the anchors are stable across runs.
    graph = nx.from_scipy_sparse_array(a_sparse)
    communities = nx.community.louvain_communities(
        graph, resolution=args.resolution, threshold=1e-09, seed=123
    )
    sizes = [len(c) for c in communities]
    keep = np.mean(sizes) + 0.5 * np.std(sizes)
    selected = [list(c) for c in communities if len(c) > keep]
    K = len(selected)
    if K < 1:
        raise ValueError("no structural communities selected; check the resolution")

    model_args = SimpleNamespace(K=K, clustertemp=args.clustertemp)
    b = 0.001  # modularity-loss weight (authors')

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

            # LIM clusters with the lowest-loss model seen, not the last one.
            best_loss = float("inf")
            best_state = None
            for _ in run.epochs(args.epochs):
                model.train()
                optimizer.zero_grad()
                pos_z, mu, r, dist = model(feat, edge, selected)
                if args.sparse_modularity:
                    modularity_loss = sparse_modularity(r, adj_sp, degree, two_m)
                else:
                    modularity_loss = model.modularity(
                        mu, r, pos_z, dist, adj_dense, test_object, model_args
                    )
                loss = b * modularity_loss
                loss.backward()
                optimizer.step()
                if loss.item() < best_loss:
                    best_loss = loss.item()
                    best_state = copy.deepcopy(model.state_dict())

            if best_state is not None:
                model.load_state_dict(best_state)
            model.eval()
            with torch.no_grad():
                _, mu, r, _ = model(feat, edge, selected)
            clusters = r.argmax(dim=1).cpu().numpy()
            run.result(clusters, num_selected_communities=K)


if __name__ == "__main__":
    main()
