"""UCoDe clustering driver on the shared ML harness.

The method is the authors' code, imported unchanged from the cloned upstream
(see build.sh / solver.json for the pinned commit): the GCN encoder
(UCODEncoder.py), loss_modularity_trace (Lossfunction.py), and the tensor
preparation in utils.py. This file assembles them and runs the training loop,
while graph and feature loading, seeding, the per-run time limit, and report
writing come from mlrunner.

It replaces a large patch to the authors' main.py that mixed those harness
concerns into their code; main.py is now left pristine and unused, and only the
compat/perf fixes in utils.py remain in ucode.patch.

Two notes on the method:
  * UCoDe's encoder does torch.bmm on a dense (1, n, n) adjacency and the loss
    needs a dense n x n modularity matrix, so it is O(n^2): it does not scale to
    large graphs, which is a result to report rather than a bug.
  * The number of communities is the encoder's output width (hid_units), not the
    unused nb_community argument to the loss. The previous integration left that
    width hardcoded at 16 and ignored the requested cluster count; here it is set
    from --clusters.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    p.add_argument("--epochs", type=int, default=1000)
    p.add_argument("--hid-dimension", type=int, default=512)
    p.add_argument("--learning-rate", type=float, default=0.001)
    p.add_argument("--weight-decay", type=float, default=0.1)


def main():
    ctx = mlrunner.setup("UCoDe graph clustering", add_arguments)
    device = ctx.use_torch()

    import networkx as nx
    import scipy.sparse as sp
    import torch
    import torch.nn as nn

    import utils
    from Lossfunction import loss_modularity_trace
    from UCODEncoder import GCN

    args = ctx.args
    sigmoid = nn.Sigmoid()

    # Dense modularity matrix and adjacency are intrinsic to UCoDe (O(n^2)).
    G = nx.from_scipy_sparse_array(ctx.graph.to_scipy_csr())
    adj_sp = nx.to_scipy_sparse_array(G)
    m = len(G.edges)
    B = utils.get_B(G)

    features_sp = sp.csr_matrix(np.ascontiguousarray(ctx.features, dtype=np.float64))
    features_t, adj_t, B_t, _ = utils.convert_torch_npz(
        adj_sp, features_sp, B, np.array([0])
    )

    nb_nodes = int(features_t.shape[1])
    ft_size = int(features_t.shape[2])
    hid_units = args.clusters  # encoder output width == number of communities

    features_t = features_t.to(device)
    adj_t = adj_t.to(device)
    B_t = B_t.to(device)

    for run in ctx.runs():
        with run:
            model = GCN(ft_size, hid_units, nb_nodes, args.hid_dimension).to(device)
            optimiser = torch.optim.Adam(
                model.parameters(),
                lr=args.learning_rate,
                weight_decay=args.weight_decay,
            )

            for _ in run.epochs(args.epochs):
                model.train()
                optimiser.zero_grad()
                logits = model(features_t, adj_t)
                loss = loss_modularity_trace(
                    logits, B_t, hid_units, hid_units, m, "non-overlap"
                )
                loss.backward()
                optimiser.step()

            model.eval()
            logits = sigmoid(model(features_t, adj_t))
            preds = torch.argmax(logits[0], dim=1).detach().cpu().numpy()
            run.result(preds)


if __name__ == "__main__":
    main()
