"""DMoN clustering driver on the shared ML harness.

The method itself is the authors' code, imported unchanged from the upstream
`graph_embedding.dmon` package (see build.sh / solver.json for the pinned
commit): the `gcn.GCN` layer, the `dmon.DMoN` pooling layer, and
`utils.normalize_graph`. This file is only the wiring the authors left to the
caller — assembling those layers into a Keras model and running the gradient
loop — plus the harness services (graph and feature loading, seeding, the
per-run time limit, and report writing), all of which come from mlrunner.

It replaces the old train_metis.py, which mixed those harness concerns into a
copy of the authors' train.py.
"""

import os
import sys
from pathlib import Path

# The authors' code is Keras 2. TF >=2.16 ships Keras 3 as tf.keras; this routes
# tf.keras back to the Keras 2 API (the tf-keras package). Must be set before
# TensorFlow is first imported, i.e. before ctx.use_tensorflow() below.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import numpy as np  # noqa: E402

import mlrunner  # noqa: E402


def add_arguments(p):
    # A fixed compute budget, not a tuned hyperparameter: the per-run time limit
    # is what actually governs how long training runs. Kept as an override.
    p.add_argument("--epochs", type=int, default=1000)
    p.add_argument(
        "--architecture",
        default="64",
        help="comma-separated GCN channel sizes; one layer per entry",
    )
    p.add_argument("--collapse-regularization", type=float, default=1.0)
    p.add_argument("--dropout-rate", type=float, default=0.5)
    p.add_argument("--learning-rate", type=float, default=0.001)


def to_sparse_tensor(matrix, tf):
    """scipy sparse -> tf.SparseTensor, as the authors' train.py did."""
    matrix = matrix.tocoo()
    return tf.sparse.SparseTensor(
        np.vstack([matrix.row, matrix.col]).T,
        matrix.data.astype(np.float32),
        matrix.shape,
    )


def main():
    ctx = mlrunner.setup("DMoN graph clustering", add_arguments)
    ctx.use_tensorflow()

    import tensorflow.compat.v2 as tf

    tf.compat.v1.enable_v2_behavior()
    from graph_embedding.dmon import dmon, gcn, utils

    args = ctx.args
    adjacency = ctx.graph.to_scipy_csr()
    n_nodes = adjacency.shape[0]
    features = tf.convert_to_tensor(np.asarray(ctx.features), dtype=tf.float32)
    feature_size = int(features.shape[1])
    architecture = [int(x) for x in str(args.architecture).split(",") if x != ""]

    graph = to_sparse_tensor(adjacency, tf)
    graph_normalized = to_sparse_tensor(utils.normalize_graph(adjacency.copy()), tf)

    def build_model():
        """Assembles the authors' layers into a Keras model (their build_dmon)."""
        input_features = tf.keras.layers.Input(shape=(feature_size,))
        input_graph = tf.keras.layers.Input((n_nodes,), sparse=True)
        input_adjacency = tf.keras.layers.Input((n_nodes,), sparse=True)
        output = input_features
        for n_channels in architecture:
            output = gcn.GCN(n_channels)([output, input_graph])
        pool, pool_assignment = dmon.DMoN(
            args.clusters,
            collapse_regularization=args.collapse_regularization,
            dropout_rate=args.dropout_rate,
        )([output, input_adjacency])
        return tf.keras.Model(
            inputs=[input_features, input_graph, input_adjacency],
            outputs=[pool, pool_assignment],
        )

    def grad(model):
        with tf.GradientTape() as tape:
            _ = model([features, graph_normalized, graph], training=True)
            loss_value = sum(model.losses)
        return tape.gradient(loss_value, model.trainable_variables)

    for run in ctx.runs():
        with run:
            model = build_model()
            optimizer = tf.keras.optimizers.Adam(args.learning_rate)
            model.compile(optimizer, None)

            for _ in run.epochs(args.epochs):
                grads = grad(model)
                optimizer.apply_gradients(zip(grads, model.trainable_variables))

            _, assignments = model(
                [features, graph_normalized, graph], training=False
            )
            clusters = assignments.numpy().argmax(axis=1)
            run.result(clusters)


if __name__ == "__main__":
    main()
