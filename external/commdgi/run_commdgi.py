import torch
import argparse
import numpy as np
import time
import gc
from torch_geometric.data import Data

# Import the necessary components from the original code
from model import Encoder, corruption, Summarizer, cluster_net
from DGI import DeepGraphInfomax

def load_metis_graph(path):
    """
    Parses a graph from a file in the METIS format.

    Args:
        path (str): The path to the METIS file.

    Returns:
        torch_geometric.data.Data: A PyTorch Geometric Data object.
    """
    with open(path, "r") as f:
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
                        edges.append([u, v - 1])
                        edge_attr.append(w)
            else:
                for v in N:
                    if v - 1 > u:  # only add each edge once
                        edges.append([u, v - 1])

    # Create the edge_index tensor for PyTorch Geometric
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

    del edges
    del edge_attr

    gc.collect()

    # Create a Data object
    data = Data(edge_index=edge_index, num_nodes=n_vertices)

    # print(f"Loaded graph from {path}:")
    # print(f"  - Nodes: {data.num_nodes}")
    # print(f"  - Edges: {data.num_edges}")

    return data

def make_adj(edge_index, num_nodes):
    adj = np.zeros((num_nodes, num_nodes), dtype=float)
    for i in range(len(edge_index[0])):
        adj[edge_index[0][i]][edge_index[1][i]] = 1
        adj[edge_index[1][i]][edge_index[0][i]] = 1  # For undirected graphs
    return adj

def make_modularity_matrix(adj):
    adj = adj * (torch.ones(adj.shape[0], adj.shape[0]) - torch.eye(adj.shape[0]))
    degrees = adj.sum(dim=0).unsqueeze(1)
    mod = adj - degrees @ degrees.t() / adj.sum()
    return mod

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metis_file', type=str, required=True, help='Path to the input graph in METIS format.')
    parser.add_argument('--output_file', type=str, required=True, help='Name of output file.')
    parser.add_argument('--K', type=int, required=True, help='How many partitions/clusters.')
    parser.add_argument('--it', type=int, default=1, help='How many clusters to compute.')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate.')
    parser.add_argument('--hidden', type=int, default=512, help='Number of hidden units.')
    parser.add_argument('--train_iters', type=int, default=1001, help='Number of training iterations.')
    parser.add_argument('--clustertemp', type=float, default=30, help='Softmax temperature for cluster assignments.')
    parser.add_argument('--seed', type=int, default=24, help='Random seed.')
    args = parser.parse_args()

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device('cpu')

    it = int(args.it)

    # 1. Load the graph from the METIS file
    data = load_metis_graph(args.metis_file).to(device)
    
    adj_all = torch.from_numpy(make_adj(data.edge_index.numpy(), data.num_nodes)).float()
    test_object = make_modularity_matrix(adj_all)


    # 2. Generate identity features since none exist
    # print("Generating identity matrix as node features.")
    data.x = torch.eye(data.num_nodes, device=device)

    for i in range(it):

        # 3. Set up the model and optimizer (logic copied from train.py)
        model = DeepGraphInfomax(
            hidden_channels=args.hidden,
            encoder=Encoder(data.num_features, args.hidden),
            summary=Summarizer(),
            corruption=corruption,
            args=args,
            cluster=cluster_net
        ).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=5e-3)

        # print('Start training...')
        start_time = time.time()
        for epoch in range(args.train_iters):
            model.train()
            optimizer.zero_grad()
            pos_z, neg_z, summary, mu, r, dist = model(data.x, data.edge_index)
            dgi_loss = model.loss(pos_z, neg_z, summary)
            modularity_loss = model.modularity(mu, r, pos_z, dist, adj_all, test_object, args)
            comm_loss = model.comm_loss(pos_z, mu)
            # loss = -modularity_loss + 5 * dgi_loss + comm_loss
            loss = -modularity_loss
            loss.backward()
            optimizer.step()
            # if epoch % 100 == 0:
            #     print(f'Epoch {epoch:03d}, Loss: {loss.item():.4f}')

        end_time = time.time()
        print(f"{end_time - start_time:.4f},", end="")

        # 4. Evaluate the model and save the cluster assignments
        # print("Evaluating and saving final cluster assignments...")
        # model.eval()
        # with torch.no_grad():
        #     _, _, _, _, r, _ = model(data.x, data.edge_index)

        # Get the final cluster for each node
        cluster_assignments = r.argmax(dim=1).cpu().numpy()

        output_file = args.output_file + str(i) + ".txt"
        # print(f"Saving vertex-to-cluster mapping to '{output_file}'")
        np.savetxt(output_file, cluster_assignments, fmt='%d')

        # print("Done.")
    
    print()

if __name__ == '__main__':
    main()