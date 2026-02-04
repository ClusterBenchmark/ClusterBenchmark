import argparse
import numpy as np
from sklearn.neighbors import NearestNeighbors

# ================================================================
# --- METIS Graph I/O --------------------------------------------
# ================================================================
def read_metis_graph(path):
    """Reads an unweighted or weighted undirected METIS .graph file.
    Returns adjacency {i: {j: weight}} with 0-based indexing."""
    adj = []
    with open(path, "r") as f:
        first = f.readline().strip().split()
        n = int(first[0])

        weighted = (len(first) >= 3 and first[2] == "01")

        for i, line in enumerate(f):
            if line.strip() == "":
                adj.append({})
                continue

            parts = line.strip().split()
            if weighted:
                # pairs: neighbor weight neighbor weight ...
                row = {}
                for a, b in zip(parts[0::2], parts[1::2]):
                    j = int(a) - 1
                    w = int(b)
                    row[j] = w
            else:
                row = {int(x) - 1: 1 for x in parts}

            adj.append(row)

    return adj, weighted


def write_metis_graph(path, adj):
    """Writes weighted graph in METIS format using '001' type."""
    n = len(adj)
    m = sum(len(row) for row in adj) // 2

    with open(path, "w") as f:
        f.write(f"{n} {m} 01\n")
        for i in range(n):
            parts = []
            for j, w in sorted(adj[i].items()):
                parts.append(f"{j+1} {w}")
            f.write(" ".join(parts) + "\n")


# ================================================================
# --- Feature File I/O --------------------------------------------
# ================================================================
def read_features(path):
    with open(path, "r") as f:
        header = f.readline().strip().split()
        n = int(header[0])
        d = int(header[1])

        X = np.zeros((n, d), dtype=float)
        for i in range(n):
            X[i] = np.array([float(x) for x in f.readline().split()])
    return X


# ================================================================
# --- Build KNN graph --------------------------------------------
# ================================================================
def build_knn_graph(X, k):
    """Return adjacency list using weight=1 (unweighted KNN)."""
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm='auto').fit(X)
    distances, indices = nbrs.kneighbors(X)

    n = X.shape[0]
    adj_knn = [dict() for _ in range(n)]

    for i in range(n):
        for j in indices[i, 1:]:  # skip self
            adj_knn[i][j] = 1
            adj_knn[j][i] = 1  # symmetrize

    return adj_knn


# ================================================================
# --- Combine Graphs ----------------------------------------------
# ================================================================
def combine_graphs(adj_orig, adj_knn, w_orig, w_knn):
    """Both input adj lists have integer weights."""
    n = len(adj_orig)
    adj = [dict() for _ in range(n)]

    for i in range(n):
        # Start with original graph
        for j in adj_orig[i]:
            adj[i][j] = adj[i].get(j, 0) + w_orig

        # Add knn graph
        for j in adj_knn[i]:
            adj[i][j] = adj[i].get(j, 0) + w_knn

    # Ensure symmetry
    for i in range(n):
        for j in list(adj[i].keys()):
            w = adj[i][j]
            adj[j][i] = w

    return adj


# ================================================================
# --- Main ---------------------------------------------------------
# ================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True, help="Input METIS .graph")
    parser.add_argument("--features", required=True, help="Input features file")
    parser.add_argument("--out", required=True, help="Output METIS .graph")
    parser.add_argument("--k", type=int, default=20, help="K in KNN graph")
    parser.add_argument("--orig_weight", type=int, default=1)
    parser.add_argument("--knn_weight", type=int, default=1)
    args = parser.parse_args()

    # print("Loading original graph...")
    adj_orig, _ = read_metis_graph(args.graph)

    # print("Loading features...")
    X = read_features(args.features)

    # print("Building KNN graph...")
    adj_knn = build_knn_graph(X, args.k)

    # print("Combining graphs...")
    adj = combine_graphs(adj_orig, adj_knn, args.orig_weight, args.knn_weight)

    # print("Writing output...")
    write_metis_graph(args.out, adj)

    # print("Done!")


if __name__ == "__main__":
    main()
