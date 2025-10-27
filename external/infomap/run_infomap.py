import sys
from infomap import Infomap
import gc
import time

def read_metis_graph(filename):
    """
    Reads an undirected graph in METIS format.
    Returns an Infomap object and the number of vertices.
    """
    im = Infomap("--flow-model undirected --silent")
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

        for u, line in enumerate(f):
            if not line.strip() or line.startswith('%'):
                continue

            N = list(map(int, line.split()))
            if vertex_weights:
                N = N[1:]

            if edge_weights:
                # Create a zip object of tuples for N
                N = zip(N[::2], N[1::2])
                for v, w in N:
                    if v - 1 > u:  # only add each edge once
                        im.add_link(u, v - 1, w)
            else:
                for v in N:
                    if v - 1 > u:  # only add each edge once
                        im.add_link(u, v - 1)
    
    gc.collect()

    return im, n_vertices


def run_infomap(im, n_vertices):
    """
    Run the Infomap community detection algorithm on the graph.
    Returns a list of cluster IDs, one per vertex, and the codelength.
    """
    im.run() 
    
    membership = [-1] * n_vertices
    max_module_id = 0
    for node in im.nodes:
        membership[node.node_id] = node.module_id
        if node.module_id > max_module_id:
            max_module_id = node.module_id

    # Assign unique cluster IDs to degree 0 vertices
    next_module_id = max_module_id + 1
    for i in range(n_vertices):
        if membership[i] == -1:
            membership[i] = next_module_id
            next_module_id += 1

    return membership, im.codelength


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
    im, n_vertices = read_metis_graph(input_file)

    if (verbose):
        print("Running Infomap clustering ...")

    for i in range(k):
        start_time = time.time()
        membership, codelength = run_infomap(im, n_vertices)
        end_time = time.time()
        elapsed = end_time - start_time

        if (verbose):
            print(f"N: {n_vertices}\nCodelength: {codelength:.4f}\nTime: {elapsed:.4f}")
            print(f"Writing cluster assignments to {output_file} ...")
        else:
            print(f"{elapsed:.4f},{codelength:.10f},", end="")
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
