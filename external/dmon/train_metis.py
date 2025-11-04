# coding=utf-8
# Copyright 2025 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Graph Clustering with Graph Neural Networks."""

from typing import Tuple
from absl import app
from absl import flags
import numpy as np
import scipy.sparse
from scipy.sparse import base
from scipy.sparse import coo_matrix
import tensorflow.compat.v2 as tf
from graph_embedding.dmon import dmon
from graph_embedding.dmon import gcn
from graph_embedding.dmon import utils
import gc
import time
from graph_embedding.dmon import metrics
tf.compat.v1.enable_v2_behavior()

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'graph_path',
    None,
    'Input graph path in METIS format.')
flags.DEFINE_string(
    'output_path',
    'clusters.txt',
    'Output path for the cluster assignments.')
flags.DEFINE_list(
    'architecture',
    [64],
    'Network architecture in the format `a,b,c,d`.')
flags.DEFINE_float(
    'collapse_regularization',
    1,
    'Collapse regularization.',
    lower_bound=0)
flags.DEFINE_float(
    'dropout_rate',
    0,
    'Dropout rate for GNN representations.',
    lower_bound=0,
    upper_bound=1)
flags.DEFINE_integer(
    'n_clusters',
    16,
    'Number of clusters.',
    lower_bound=0)
flags.DEFINE_integer(
    'n_epochs',
    1000,
    'Number of epochs.',
    lower_bound=0)
flags.DEFINE_float(
    'learning_rate',
    0.001,
    'Learning rate.',
    lower_bound=0)
flags.DEFINE_integer(
    'n_runs',
    1,
    'Number of times to run the clustering.',
    lower_bound=1)


def load_metis(filename):
    """Parses a METIS file and returns the adjacency matrix.

    Args:
      filename: A valid file name of a METIS file.

    Returns:
      A sparse adjacency matrix of a graph.
    """
    with open(filename, "r") as f:
        # Skip comment lines
        first_line = ""
        for line in f:
            if line.strip() and not line.startswith('%'):
                first_line = line.strip()
                break

        parts = first_line.split()
        n_vertices = int(parts[0])
        n_edges = int(parts[1])
        t = 0
        if (len(parts) > 2):
            t = int(parts[2])

        vertex_weights = (t == 10 or t == 11)
        edge_weights = (t == 1 or t == 11)

        row = []
        col = []
        data = []

        for u, line in enumerate(f):
            if not line.strip() or line.startswith('%'):
                continue

            N = list(map(int, line.split()))
            if vertex_weights:
                N = N[1:]

            if edge_weights:
                N = zip(N[::2], N[1::2])
                for v, w in N:
                    row.append(u)
                    col.append(v - 1)
                    data.append(w)
            else:
                for v in N:
                    row.append(u)
                    col.append(v - 1)

    if not edge_weights:
        data = [1 for _ in range(len(row))]

    adj = coo_matrix((data, (row, col)), shape=(n_vertices, n_vertices))

    del row
    del col
    del data

    gc.collect()

    return adj


def convert_scipy_sparse_to_sparse_tensor(
    matrix):
  """Converts a sparse matrix and converts it to Tensorflow SparseTensor."""
  matrix = matrix.tocoo()
  return tf.sparse.SparseTensor(
      np.vstack([matrix.row, matrix.col]).T, matrix.data.astype(np.float32),
      matrix.shape)


def build_dmon(
    input_features,
    input_graph,
    input_adjacency):
  """Builds a Deep Modularity Network (DMoN) model from the Keras inputs."""
  output = input_features
  for n_channels in FLAGS.architecture:
    output = gcn.GCN(n_channels)([output, input_graph])
  pool, pool_assignment = dmon.DMoN(
      FLAGS.n_clusters,
      collapse_regularization=FLAGS.collapse_regularization,
      dropout_rate=FLAGS.dropout_rate)([output, input_adjacency])
  return tf.keras.Model(
      inputs=[input_features, input_graph, input_adjacency],
      outputs=[pool, pool_assignment])

def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')
  
  # Load and process the data once.
  adjacency = load_metis(FLAGS.graph_path)
  adjacency = adjacency.tocsr()
  n_nodes = adjacency.shape[0]
  features = scipy.sparse.identity(n_nodes, dtype=np.float32)
  features = features.todense()
  features = tf.convert_to_tensor(features, dtype=tf.float32)
  feature_size = features.shape[1]
  graph = convert_scipy_sparse_to_sparse_tensor(adjacency)
  graph_normalized = convert_scipy_sparse_to_sparse_tensor(
      utils.normalize_graph(adjacency.copy()))

  for i in range(FLAGS.n_runs):
    output_path = f'{FLAGS.output_path}{i}.txt'

    start_time = time.time()

    # Create model input placeholders of appropriate size
    input_features = tf.keras.layers.Input(shape=(feature_size,))
    input_graph = tf.keras.layers.Input((n_nodes,), sparse=True)
    input_adjacency = tf.keras.layers.Input((n_nodes,), sparse=True)

    model = build_dmon(input_features, input_graph, input_adjacency)

    def grad(model, inputs):
      with tf.GradientTape() as tape:
        _ = model(inputs, training=True)
        loss_value = sum(model.losses)
      return model.losses, tape.gradient(loss_value, model.trainable_variables)

    optimizer = tf.keras.optimizers.Adam(FLAGS.learning_rate)
    model.compile(optimizer, None)

    for epoch in range(FLAGS.n_epochs):
      loss_values, grads = grad(model, [features, graph_normalized, graph])
      optimizer.apply_gradients(zip(grads, model.trainable_variables))

    # Obtain the cluster assignments.
    _, assignments = model([features, graph_normalized, graph], training=False)
    assignments = assignments.numpy()
    clusters = assignments.argmax(axis=1)

    end_time = time.time()
    computation_time = end_time - start_time

    modularity = metrics.modularity(adjacency, clusters)

    print(f'{computation_time:.4f},{modularity:.4f},', end='')

    # Save the cluster assignments.
    with open(output_path, 'w') as f:
      for cluster in clusters:
        f.write(f'{cluster}\n')

  print()


if __name__ == '__main__':
  app.run(main)
