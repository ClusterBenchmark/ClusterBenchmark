import sys
import igraph as ig
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

        g = ig.Graph(n=n_vertices, edges=edges)

    if edge_weights:
        g.es["weight"] = edge_attr

    del edges
    del edge_attr

    gc.collect()

    return g


def run_louvain(g):
    """
    Run the Louvain community detection algorithm on the graph.
    Returns a list of cluster IDs, one per vertex.
    """
    clusters = g.community_multilevel()
    membership = clusters.membership

    if "weight" in g.edge_attributes():
        modularity = g.modularity(clusters.membership, weights=g.es["weight"])
    else:
        modularity = clusters.modularity
    return membership, modularity


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <input.metis> <output_file> <verbose> <k>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    verbose = int(sys.argv[3])
    k = int(sys.argv[4])

    if (verbose):
        print(f"Reading graph from {input_file} ...")
    g = read_metis_graph(input_file)

    if (verbose):
        print("Running Louvain clustering ...")

    for i in range(k):
        start_time = time.time()
        membership, modularity = run_louvain(g)
        end_time = time.time()
        elapsed = end_time - start_time

        if (verbose):
            print(f"N: {len(g.vs)}\nModularity: {modularity:.4f}\nTime: {elapsed:.4f}")
            print(f"Writing cluster assignments to {output_file} ...")
        else:
            print(f"{elapsed:.4f},{modularity:.10f},", end="")
            sys.stdout.flush()

        with open(output_file + str(i) + ".txt", "w") as out:
            out.write("\n".join(map(str, membership)))
            out.write("\n")

    if (verbose):
        print("Done.")
    else:
        print()

if __name__ == "__main__":
    main()
