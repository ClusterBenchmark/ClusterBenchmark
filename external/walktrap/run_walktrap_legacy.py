import sys
import igraph as ig
import gc
import time
import argparse
import multiprocessing
import queue


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


def run_walktrap(g):
    """
    Run the Walktrap community detection algorithm on the graph.
    Returns a list of cluster IDs, one per vertex.
    """
    dendrogram = g.community_walktrap()
    clusters = dendrogram.as_clustering()
    membership = clusters.membership

    if "weight" in g.edge_attributes():
        modularity = g.modularity(clusters.membership, weights=g.es["weight"])
    else:
        modularity = clusters.modularity
    return membership, modularity

def run_walktrap_worker(g, result_queue):
    """
    A worker function to run walktrap in a separate process.
    Puts the result in a queue.
    """
    try:
        membership, modularity = run_walktrap(g)
        result_queue.put((membership, modularity))
    except Exception as e:
        # Pass exceptions back to the main process
        result_queue.put(e)

def main():
    parser = argparse.ArgumentParser(description="Run Walktrap clustering.")
    parser.add_argument("--input_file", help="Path to the input graph file in METIS format.")
    parser.add_argument("--output_file", help="Base name for output cluster files.")
    parser.add_argument("--verbose", type=int, help="Enable verbose output.")
    parser.add_argument("--k", type=int, help="Number of times to run the clustering.")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout in seconds for each clustering run. Default is 0 (no timeout).")
    args = parser.parse_args()

    if (args.verbose):
        print(f"Reading graph from {args.input_file} ...")
    g = read_metis_graph(args.input_file)

    if (args.verbose):
        print("Running Walktrap clustering ...")

    for i in range(args.k):
        gc.collect()

        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=run_walktrap_worker, args=(g, result_queue))
        
        start_time = time.time()
        p.start()

        try:
            # Wait for the result with a timeout
            if args.timeout > 0:
                result = result_queue.get(timeout=args.timeout)
            else:
                result = result_queue.get()

            if isinstance(result, Exception):
                raise result

            membership, modularity = result
            end_time = time.time()
            elapsed = end_time - start_time

            if (args.verbose):
                print(f"N: {len(g.vs)}\nModularity: {modularity:.4f}\nTime: {elapsed:.4f}")
                print(f"Writing cluster assignments to {args.output_file} ...")
            else:
                print(f"{elapsed:.4f},{modularity:.10f},", end="")
                sys.stdout.flush()

            with open(args.output_file + str(i) + ".txt", "w") as out:
                out.write("\n".join(map(str, membership)))
                out.write("\n")
        except queue.Empty:
            if (args.verbose):
                print("Clustering timed out.")
            else:
                print("tle,tle,", end="")
                sys.stdout.flush()
            # The file for this run won't be created, so the calling script will know it failed.
            continue
        except Exception as e:
            if (args.verbose):
                print(f"An error occurred during clustering: {e}")
            else:
                print("err,err,", end="")
                sys.stdout.flush()
            continue
        finally:
            # Ensure the process is terminated and joined
            if p.is_alive():
                p.terminate()
            p.join()


    if (args.verbose):
        print("Done.")
    else:
        print()

if __name__ == "__main__":
    main()