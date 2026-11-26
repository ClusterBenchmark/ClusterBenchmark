import sys
import igraph as ig
import gc
import time
import multiprocessing
import queue
import argparse

from cdlib import algorithms
from cdlib import evaluation
import networkx as nx

def read_metis_graph(filename):
    """
    Reads an undirected graph in METIS format.
    Returns a networkx.Graph object.
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

        g = nx.Graph()
        g.add_nodes_from(range(n_vertices))

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
                        g.add_edge(u, v - 1, weight=w)
            else:
                for v in N:
                    if v - 1 > u:  # only add each edge once
                        g.add_edge(u, v - 1)

    gc.collect()

    return g


def run_cnm(g):
    """
    Run the CNM community detection algorithm on a networkx graph.
    Returns a list of cluster IDs, one per vertex, and the modularity score.
    """
    # The graph 'g' is expected to be a networkx graph.
    coms = algorithms.greedy_modularity(g)
    modularity = evaluation.newman_girvan_modularity(g, coms).score

    # The returned 'coms' object also contains the list of communities.
    # We need to convert this into a membership vector where the i-th
    # element is the community ID of the i-th vertex.
    # The nodes in the graph are integers, so they can be used directly as indices.
    membership_vector = [0] * g.number_of_nodes()
    for i, community in enumerate(coms.communities):
        for node_index in community:
            membership_vector[node_index] = i

    return membership_vector, modularity


def run_cnm_worker(g, result_queue):
    """
    A worker function to run Louvain in a separate process.
    Puts the result in a queue.
    """
    try:
        membership, modularity = run_cnm(g)
        result_queue.put((membership, modularity))
    except Exception as e:
        # Pass exceptions back to the main process
        result_queue.put(e)


def main():
    parser = argparse.ArgumentParser(description="Run CNM clustering.")
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
        print("Running CNM clustering ...")

    for i in range(args.k):
        gc.collect()
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=run_cnm_worker, args=(g, result_queue))

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
                print(f"N: {g.number_of_nodes()}\nModularity: {modularity:.4f}\nTime: {elapsed:.4f}")
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
