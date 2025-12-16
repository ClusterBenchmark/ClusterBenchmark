import sys
import networkx as nx
import bayanpy
import argparse
import multiprocessing
import gc
import time

def read_metis_graph(filename):
    """
    Reads an undirected graph in METIS format.
    Returns an igraph.Graph object.
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

        edges = []
        edge_attr = []

        for u, line in enumerate(f):
            if not line.strip() or line.startswith('%'):
                continue

            N = list(map(int, line.split()))
            if vertex_weights:
                N = N[1:]

            if edge_weights:
                N = zip(N[::2], N[1::2])
                for v, w in N:
                    if v - 1 > u:  # only add each edge once
                        edges.append((u, v - 1))
                        edge_attr.append(w)
            else:
                for v in N:
                    if v - 1 > u:  # only add each edge once
                        edges.append((u, v - 1))

        g = nx.Graph(edges)

    del edges
    del edge_attr

    gc.collect()

    return g

def main():
    parser = argparse.ArgumentParser(description="Run Bayan clustering.")
    parser.add_argument("--input_file", help="Path to the input graph file in METIS format.")
    parser.add_argument("--output_file", help="Base name for output cluster files.")
    args = parser.parse_args()

    print(f"Reading graph from {args.input_file} ...")
    
    g = read_metis_graph(args.input_file)

    if g.number_of_edges() > 3000:
        print(f"Too many vertices")
        return 0

    print("Running Bayan clustering ...")

    modularity, optimality_gap, community, modeling_time, solve_time = bayanpy.bayan(g, threshold=0.001, time_allowed=3600, resolution=1)

    print(f"Elapsed {solve_time + modeling_time:.4f}")

    membership = [0 for _ in range(g.number_of_nodes())]
    for c in range(len(community)):
        for u in community[c]:
            membership[u] = c

    with open(args.output_file, "w") as out:
        for u in range(g.number_of_nodes()):
            out.write(f"{membership[u]}\n")

    print("Done.")

if __name__ == "__main__":
    main()
