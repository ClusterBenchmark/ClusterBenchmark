#                                                                            
#    Copyright 2022
#    Alexander Belyi <alexander.belyi@gmail.com>,
#    Stanislav Sobolevsky <sobolevsky@nyu.edu>                                               
#                                                                            
#    This file contains the source code of the GNNS algorithm and its evaluation.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import gc
import time
import torch
import random
import numpy as np
import scipy
import networkx as nx
import argparse

class Engine:
    def __init__(self, engine: str) -> None:
        if engine == 'np':
            self.array = self.array_np
            self.sparse_array = self.sparse_array_np
            self.diag = self.diag_np
            self.sum = self.sum_np
            self.sparse_sum = self.sparse_sum_np
            self.mean = self.mean_np
            self.max = self.max_np
            self.argmax = self.argmax_np
            self.eye = self.eye_np
            self.ones = self.ones_np
            self.zeros = self.zeros_np
            self.abs = self.abs_np
            self.exp = self.exp_np
            self.concatenate = self.concatenate_np
            self.reshape = self.reshape_np
            self.transpose = self.transpose_np
            self.tile = self.tile_np
            self.matmul = self.matmul_np
            self.random_uniform = self.random_uniform_np
            self.to_sparse_csr = self.to_sparse_csr_np
            self.cuda = self.identity_np
            self.numpy = self.identity_np
        elif engine == 'torch':
            self.device = torch.device('cpu')
            self.cuda_available = False
            if torch.cuda.is_available():
                self.cuda_available = True
                self.device = torch.device(0)
            self.array = self.array_torch
            self.sparse_array = self.sparse_array_torch
            self.diag = self.diag_torch
            self.sum = self.sum_torch
            self.sparse_sum = self.sparse_sum_torch
            self.mean = self.mean_torch
            self.max = self.max_torch
            self.argmax = self.argmax_torch
            self.eye = self.eye_torch
            self.ones = self.ones_torch
            self.zeros = self.zeros_torch
            self.abs = self.abs_torch
            self.exp = self.exp_torch
            self.concatenate = self.concatenate_torch
            self.reshape = self.reshape_torch
            self.transpose = self.transpose_torch
            self.tile = self.tile_torch
            self.matmul = self.matmul_torch
            self.random_uniform = self.random_uniform_torch
            self.to_sparse_csr = self.to_sparse_csr_torch
            self.cuda = self.cuda_torch
            self.numpy = self.numpy_torch

    def array_np(self, x, device=None):
        return np.array(x)

    def sparse_array_np(self, x, device=None):
        if type(x) == scipy.sparse.csr_matrix:
            return x
        return scipy.sparse.csr_matrix(x)

    def diag_np(self, x):
        return np.diag(x)

    def sum_np(self, x, axis=None, keepdims=False):
        return np.sum(x, axis=axis, keepdims=keepdims)

    def sparse_sum_np(self, x, axis=None):
        return np.array(np.sum(x, axis=axis))

    def mean_np(self, x, axis=None, keepdims=False):
        return np.mean(x, axis=axis, keepdims=keepdims)
    
    def max_np(self, x, axis=None, keepdims=False):
        return np.max(x, axis=axis, keepdims=keepdims)

    def argmax_np(self, x, axis=None): 
        return np.argmax(x, axis=axis)

    def eye_np(self, size, dtype=None, device=None):
        return np.eye(size, dtype=dtype)

    def ones_np(self, size, dtype=None, device=None):
        return np.ones(size, dtype=dtype)

    def zeros_np(self, size, dtype=None, device=None):
        return np.zeros(size, dtype=dtype)

    def abs_np(self, x):
        return np.abs(x)

    def exp_np(self, x):
        return np.exp(x)

    def concatenate_np(self, x, axis=None):
        return np.concatenate(x, axis=axis)
    
    def reshape_np(self, x, shape):
        return np.reshape(x, shape)

    def transpose_np(self, x, axis1, axis2):
        return np.swapaxes(x, axis1, axis2)

    def tile_np(self, x, shape):
        return np.tile(x, shape)

    def matmul_np(self, x, y):
        return np.matmul(x, y)

    def random_uniform_np(self, low, high, size, device="cpu"):
        return np.random.uniform(low=low, high=high, size=size)

    def to_sparse_csr_np(self, x):
        return x.tocsr()

    def identity_np(self, x):
        return x

    def array_torch(self, x, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        return torch.tensor(x, device=device)

    def sparse_array_torch(self, x, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        coo_x = scipy.sparse.coo_matrix(x)
        return torch.sparse_coo_tensor(np.vstack((coo_x.row, coo_x.col)), coo_x.data, size=coo_x.shape, device=device)

    def diag_torch(self, x):
        return torch.diag(x)

    def sum_torch(self, x, axis=None, keepdims=False):
        return torch.sum(x, axis=axis, keepdims=keepdims)

    def sparse_sum_torch(self, x, axis=None):
        return torch.sparse.sum(x, dim=axis).to_dense()

    def mean_torch(self, x, axis=None, keepdims=False):
        return torch.mean(x, axis=axis, keepdims=keepdims)
    
    def max_torch(self, x, axis=None, keepdims=False):
        if axis is None:
            return torch.max(x, axis=axis, keepdims=keepdims)
        else:
            return torch.max(x, axis=axis, keepdims=keepdims).values

    def argmax_torch(self, x, axis=None, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        return torch.argmax(x, axis=axis).to(device)

    def eye_torch(self, size, dtype=None, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        return torch.eye(size, dtype=dtype, device=device)

    def ones_torch(self, size, dtype=None, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        return torch.ones(size, dtype=dtype, device=device)

    def zeros_torch(self, size, dtype=None, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        return torch.zeros(size, dtype=dtype, device=device)

    def abs_torch(self, x):
        return torch.abs(x)

    def exp_torch(self, x):
        return torch.exp(x)

    def concatenate_torch(self, x, axis=0):
        return torch.cat(x, dim=axis)
    
    def reshape_torch(self, x, shape):
        return torch.reshape(x, shape)

    def transpose_torch(self, x, dim0, dim1):
        return torch.transpose(x, dim0, dim1)

    def tile_torch(self, x, shape):
        return torch.tile(x, shape)

    def matmul_torch(self, x, y):
        return torch.matmul(x, y)

    def random_uniform_torch(self, low, high, size, dtype=None, device="cpu"):
        if not self.cuda_available:
            device = "cpu"
        return torch.zeros(size, dtype=dtype, device=device).uniform_(low, high)

    def to_sparse_csr_torch(self, x):
        return x.to_sparse_csr()

    def cuda_torch(self, x):
        if not self.cuda_available:
            return x
        return x.cuda()
    
    def numpy_torch(self, x):
        return x.cpu().numpy()


def set_all_random_seeds(seed=1):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)


def get_modularity_matrix(G, symmetrize=True, loops_style=2, device="cpu"):
    A = nx.to_numpy_array(G)
    A = eng.array(A, device)
    if loops_style == 2 and not G.is_directed():
        A += eng.diag(eng.diag(A))
    elif loops_style == 0:
        A -= eng.diag(eng.diag(A))
    w_in = A.sum(axis=0, keepdims=True)
    w_out = A.sum(axis=1, keepdims=True)
    T = w_out.sum()
    Q = A / T - w_out @ w_in / (T ** 2)
    if symmetrize:
        Q = (Q + Q.T) / 2
    return Q

def get_sparse_modularity_matrix(G, loops_style=2, device="cpu"):
    A = nx.adjacency_matrix(G, dtype=np.float64)
    if loops_style == 2 and not G.is_directed():
        A.setdiag(A.diagonal() * 2)
    elif loops_style == 0:
        A.setdiag(0)
    Q_diag = eng.array(A.diagonal(), device)
    A = eng.sparse_array(A, device)
    w_in = eng.sparse_sum(A, axis=0).reshape((1, A.shape[0]))
    w_out = eng.sparse_sum(A, axis=1).reshape((A.shape[0], 1))
    T = w_out.sum()
    w_in /= T
    w_out /= T
    Q = A / T
    Q_diag /= T
    Q = eng.to_sparse_csr(Q)
    return Q, Q_diag, w_out, w_in


class GNNSModularityOptimizer():
    def __init__(self, G, strip_diagonal=True, normalize_modularity=False,
                 normalize_each_step=True, normalize_QC=True, use_sparse=False):
        self.num_model_params = 2
        self.net_size = len(G)
        self.normalize_modularity = normalize_modularity
        self.use_sparse = use_sparse
        self.strip_diagonal = strip_diagonal
        if self.use_sparse:
            self.sparse_Q, self.Q_diag, self.w_out, self.w_in = get_sparse_modularity_matrix(G, device="cuda:0")
            self.Q_diag = eng.reshape(self.Q_diag, (1, self.net_size, 1))
            self.Q_diag -= eng.reshape(self.w_out * eng.transpose(self.w_in, 0, 1), (1, self.net_size, 1))
        else:
            self.Q = get_modularity_matrix(G, symmetrize=True, device="cuda:0")
            self.Q_diag = eng.reshape(eng.diag(self.Q), (1, self.net_size, 1))
        self.reshape_Q()
        self.normalize_each_step = normalize_each_step
        self.normalize_QC = normalize_QC

    def reshape_Q(self):
        if self.use_sparse:
            self.w_out = self.w_out[None, :, :]
            self.w_in = self.w_in[None, :, :]
        else:
            self.Q = self.Q.reshape((1, *self.Q.shape)) # add batch dimension
            if self.normalize_modularity:
                w = eng.sum(eng.abs(self.Q), axis=2, keepdims=True)
                self.Q /= w + (w==0)

    def reshape_model_params(self, params):
        f0 = eng.cuda(-params[:, 0:1, None])
        f1 = eng.cuda(params[:, 1:2, None])
        f2 = 1.0 - f0 - f1
        return f0, f1, f2

    def discretize(self):
        c = eng.argmax(self.C, axis=2)
        self.C[:,:,:] = 0
        for i in range(self.batch_size):
            self.C[i, range(self.net_size), c[i, :]] = 1

    def calculate_modularity(self):
        QxC = self.Q_times_C(False)
        q = eng.matmul(self.C.reshape((self.batch_size, 1, -1)), QxC.reshape((self.batch_size, -1, 1))).reshape((-1,))
        return q

    def activation(self,x): #ReLU
        return x * (x>0)

    def Q_times_C(self, strip_diagonal):
        if self.use_sparse:
            C = eng.transpose(self.C, 0, 1).reshape((self.net_size, -1))
            QxC = eng.transpose((self.sparse_Q @ C).reshape((self.net_size, self.batch_size, -1)), 1, 0)
            QxC -= eng.matmul(self.w_out, eng.matmul(self.w_in, self.C))
        else:
            QxC = eng.matmul(self.Q, self.C)
        if strip_diagonal:
            return QxC - self.Q_diag * self.C
        else:
            return QxC

    def calculate(self, params, init_partition, num_iterations, discretize_result=False):
        self.batch_size = init_partition.shape[0]
        f0, f1, f2 = self.reshape_model_params(params)
        self.C = init_partition
        self.normalize_attachments()
        for _ in range(num_iterations):
            QxC = self.Q_times_C(self.strip_diagonal)
            if self.normalize_QC:
                t = eng.abs(eng.max(QxC, axis=2, keepdims=True))
                QxC /= t + (t == 0)
            bias = eng.ones((self.batch_size, self.net_size, 1), dtype=float, device="cuda:0")
            next_C = f0 * bias + f1 * self.C + f2 * QxC
            self.C = self.activation(next_C)
            self.normalize_attachments()
        if discretize_result:
            self.discretize()
        mod = self.calculate_modularity()
        return self.C, mod

    def normalize_attachments(self):
        if self.normalize_each_step:
            w = eng.sum(self.C, axis=2, keepdims=True)
            self.C /= w + (w==0)


def runGNNSSeries(G, max_num_communities, iterations_per_stage, num_random_configs, fraction_to_keep,
                discretize_last=True, init_params=None, init_communities=None, alpha=0.0, manual_gc=True, verbose=0):
    num_model_params = 2
    net_size = len(G)
    max_batch_size = hypers.get('max_batch_size', 1000)
    max_total_tensor_size = hypers.get('max_total_tensor_size', 200_000_000)
    max_batch_size = max(1, min(max_batch_size, int(max_total_tensor_size / (net_size * max_num_communities))))
    start_time = time.time()
    GNNS = GNNSModularityOptimizer(G, strip_diagonal=hypers.get('strip_diagonal', True),
                                    normalize_modularity=hypers.get('normalize_modularity', False),
                                    normalize_each_step=hypers.get('normalize_each_step', True),
                                    use_sparse=hypers.get('use_sparse', False))
    final_modularities = np.empty(0)
    best_modularity = -1
    for i in range((num_random_configs + max_batch_size - 1) // max_batch_size):
        cur_range = (i * max_batch_size, min((i + 1) * max_batch_size, num_random_configs))
        batch_size = cur_range[1] - cur_range[0]
        if init_params is None:
            params = eng.random_uniform(low=0, high=1.0, size=(batch_size, num_model_params), device="cuda:0")
        else:
            params = eng.tile(init_params.flatten(), (batch_size, 1))
        if init_communities is None:
            partition = eng.random_uniform(low=0, high=1.0, size=(batch_size, len(G), max_num_communities), device="cuda:0")
        else:
            partition = eng.tile(init_communities, (batch_size, 1, 1))
        for stage in range(len(iterations_per_stage)):
            discretize = discretize_last and (stage == len(iterations_per_stage) - 1)
            communities, modularities = GNNS.calculate(params, partition, iterations_per_stage[stage], discretize_result=discretize)
            modularities = eng.numpy(modularities)
            index_best = np.argmax(modularities)
            if verbose > 0:
                print('Stage {} completed'.format(stage+1))
                print('Top modularity={}, mean={}, best_parameters={}'.format(modularities[index_best], np.mean(modularities), params[index_best]))
            if stage < len(iterations_per_stage) - 1:
                next_batch_size = max(1, batch_size * iterations_per_stage[0] // iterations_per_stage[stage+1])
                selected_indices = modularities >= sorted(modularities)[-max(1, int(next_batch_size * fraction_to_keep))]
                params = params[selected_indices, :]
                partition = communities[selected_indices]
                num_to_keep = sum(selected_indices)
                num_to_repeat = next_batch_size - num_to_keep
                if num_to_repeat > 0:
                    weights = np.exp(modularities[selected_indices] * alpha)
                    weights = weights / sum(weights)
                    indices_to_repeat_partition = np.random.choice(num_to_keep, size=num_to_repeat, p=weights)
                    repeated_partition = partition[indices_to_repeat_partition]
                    partition = eng.concatenate([partition, repeated_partition], axis=0)
                    new_params = eng.random_uniform(low=0, high=1.0, size=(num_to_repeat, num_model_params), device="cuda:0")
                    params = eng.concatenate([params, new_params], axis=0)
        final_modularities = np.concatenate([final_modularities, modularities])
        if modularities.size > 0 and modularities[index_best] > best_modularity:
            best_modularity = modularities[index_best]
            best_communities = communities[index_best, :]
            best_parameters = params[index_best]
        if manual_gc:
            del params, partition
            gc.collect()
            torch.cuda.empty_cache()
    if manual_gc:
        del GNNS
        gc.collect()
        torch.cuda.empty_cache()
    return best_communities, modularities, best_parameters, best_modularity, time.time()-start_time

def read_metis_graph(filename):
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

        G = nx.Graph()
        G.add_nodes_from(range(n_vertices))

        for u, line in enumerate(f):
            if not line.strip() or line.startswith('%'):
                continue

            N = list(map(int, line.split()))
            if vertex_weights:
                N = N[1:]

            if edge_weights:
                N = zip(N[::2], N[1::2])
                for v, w in N:
                    G.add_edge(u, v - 1)
            else:
                for v in N:
                    G.add_edge(u, v - 1)

    gc.collect()

    return G

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input graph in METIS format")
    parser.add_argument("output", help="Output file for clustering")
    parser.add_argument("K", type=int, help="Number of clusterings to produce")
    parser.add_argument("--num-communities", type=int, help="Number of communities to find")
    args = parser.parse_args()

    G = read_metis_graph(args.input)

    torch.set_default_dtype(torch.float64)

    global hypers, eng
    hypers = {}
    hypers['ENGINE'] = 'torch'
    eng = Engine(hypers['ENGINE'])

    hypers['seed'] = 13
    hypers['strip_diagonal'] = True
    hypers['normalize_modularity'] = False
    hypers['normalize_each_step'] = True
    hypers['use_sparse'] = True
    hypers['max_batch_size'] = 1000
    hypers['max_total_tensor_size'] = 100_000_000
    hypers["num_processes"] = 4
    
    set_all_random_seeds(hypers['seed'])
    iterations_per_stage = [10, 10, 30]
    num_initial_GNNS_configs = 100
    fraction_to_keep = 1/3
    
    num_communities = args.num_communities
    if not num_communities:
        num_communities = int(np.sqrt(len(G)))

    for i in range(args.K):
        start_time = time.time()
        C, _, _, _, _ = runGNNSSeries(G, max_num_communities = num_communities,
                                                    iterations_per_stage=iterations_per_stage,
                                                    num_random_configs=num_initial_GNNS_configs,
                                                    fraction_to_keep=fraction_to_keep,
                                                    manual_gc=(len(G) > 1000),
                                                    verbose=0)
        end_time = time.time()
        
        partition = C.argmax(axis=1)
        
        output_filename = f"{args.output}_gnns_{i}.txt"
        with open(output_filename, 'w') as f:
            for node_id in range(len(partition)):
                f.write(str(partition[node_id]) + '\n')
        
        print(f"{end_time - start_time},", end="")

    print()


if __name__ == "__main__":
    main()