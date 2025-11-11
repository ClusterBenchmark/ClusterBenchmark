import sys
from infomap import Infomap
import gc
import time
import argparse
import multiprocessing
import queue

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


def run_infomap_worker(im, n_vertices, result_queue):
    """
    A worker function to run Infomap in a separate process.
    Puts the result in a queue.
    """
    try:
        membership, codelength = run_infomap(im, n_vertices)
        result_queue.put((membership, codelength))
    except Exception as e:
        # Pass exceptions back to the main process
        result_queue.put(e)


def main():
    parser = argparse.ArgumentParser(description="Run Infomap clustering.")
    parser.add_argument("--input_file", help="Path to the input graph file in METIS format.")
    parser.add_argument("--output_file", help="Base name for output cluster files.")
    parser.add_argument("--verbose", type=int, help="Enable verbose output.")
    parser.add_argument("--k", type=int, help="Number of times to run the clustering.")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout in seconds for each clustering run. Default is 0 (no timeout).")
    args = parser.parse_args()

    if (args.verbose):
        print(f"Reading graph from {args.input_file} ...")
    im, n_vertices = read_metis_graph(args.input_file)

    if (args.verbose):
        print("Running Infomap clustering ...")

    for i in range(args.k):
        gc.collect()

        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=run_infomap_worker, args=(im, n_vertices, result_queue))
        
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

            membership, codelength = result
            end_time = time.time()
            elapsed = end_time - start_time

            if (args.verbose):
                print(f"N: {n_vertices}\nCodelength: {codelength:.4f}\nTime: {elapsed:.4f}")
                print(f"Writing cluster assignments to {args.output_file} ...")
            else:
                print(f"{elapsed:.4f},{codelength:.10f},", end="")
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
