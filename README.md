# From Heuristics to Graph Neural Networks: Benchmarking Modularity Maximization for Community Detection

**Authors:** Adil Chhabra, Kenneth Langedal, and Christian Schulz <br>
**Status:** In progress

## Overview

This repository provides the benchmarking framework and implementations used in our survey paper, **"From Heuristics to Graph Neural Networks: Benchmarking Modularity Maximization for Community Detection."**

The primary contribution of this survey is a unified interface for benchmarking diverse clustering algorithms using a single, standardized graph format. This allows for direct comparison between traditional heuristic solvers and modern GNN-based approaches.

### Repository Structure

## Requirements

* A C compiler and `make` (build the `CONVERT` and `EVAL` tools).
* Python 3.12 with a working `venv` + `pip`.
* An **MPI** implementation (e.g. OpenMPI) — needed only by the C/C++ solvers `clustre` and `vieclus`, whose KaHIP/VieClus/KaGen stack links against it. The other solvers do not require MPI.
* *Optional:* a CUDA toolkit and a GPU for accelerated runs of the learning-based solvers. A CUDA build also runs on CPU, so a GPU is optional.

Each solver's `build.sh` provisions its own isolated environment (a Python virtual environment, or a cloned + patched + compiled binary), so the solvers never share dependencies.

<details>
<summary><b>No sudo?</b> Installing Python and MPI in user space</summary>

If you cannot install `python3.12-venv`, get a self-contained interpreter with [uv](https://docs.astral.sh/uv/) (no root needed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"          # add to ~/.bashrc to persist
uv python install 3.12
ln -sf "$(ls -d "$(uv python dir)"/cpython-3.12*/bin/python3 | head -1)" "$HOME/.local/bin/python3"
hash -r
```

OpenMPI likewise builds into `$HOME/.local` without root:

```bash
./configure --prefix="$HOME/.local" --disable-mpi-fortran && make -j"$(nproc)" && make install
export LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH"   # add to ~/.bashrc to persist
```
</details>

## Setup

```bash
make                                              # builds CONVERT and EVAL
python3 -m venv scripts/.venv                     # tooling venv (instance prep + tuning)
scripts/.venv/bin/pip install numpy optuna
for d in external/*/; do [ -f "$d/build.sh" ] && bash "$d/build.sh" cpu; done   # cpu or cuda
```

`build.sh` accepts `cpu` or `cuda` for the learning-based solvers (selecting CPU-only or CUDA wheels); the classical solvers ignore the argument.

## Preparing instances

The harness reads a compact **binary CSR** graph and, optionally, a **binary feature** file. Convert a METIS `.graph` (and its sibling `.features`, if any) once — useful when the source data lives on read-only storage:

```bash
scripts/prep_instances.sh <out_dir> path/to/graph1.graph [graph2.graph ...]
```

This writes `<name>.csr` (and `<name>.feat` when features exist) into the writable `<out_dir>`. Ground-truth `.labels` are read in place and are not copied.

## Running the benchmark

Every solver is driven through a single harness with a uniform command line; everything solver-specific is declared in `external/<solver>/solver.json`. A single run:

```bash
python3 scripts/harness.py --solver leiden \
    --graph <out_dir>/cora.csr --labels path/to/cora.labels \
    --runs 5 --time 3600 --memory 120 --threads 1 --device cpu \
    --out results/leiden.jsonl
```

Key options: `--runs` (repeats, run `i` uses seed `base+i`), `--time` (per-run seconds), `--memory` (GB, hard-capped per solver via cgroups — leave some headroom below physical RAM), `--threads`, `--device cpu|cuda`, `--features <file>.feat` (attached automatically only for solvers that consume features), and `--clusters` (`auto` by default, derived from the solver's policy). A per-run **watchdog** hard-kills any run that exceeds `--time` plus a grace margin (`--grace`, `--startup-grace`), so a solver that ignores its own limit — or is stuck in a C extension where a signal cannot fire — is still stopped. Output is JSON Lines, one full record per run; `scripts/export_csv.py` produces the flat CSV if you want it.

**Protocol A (out-of-the-box).** Run every solver over a set of prepared instances with author-faithful defaults — real features where the instance has them, synthetic LDP+RNI otherwise:

```bash
scripts/run_protocol_a.sh <csr_dir> <labels_dir> results_A  cpu 3600 120 5 1
# args: CSR_DIR LABELS_DIR OUT_DIR [DEVICE TIME MEM_GB RUNS THREADS GRACE STARTUP_GRACE]
```

Override the solver set with the `SOLVERS` environment variable (e.g. `SOLVERS="leiden vieclus" scripts/run_protocol_a.sh ...`).

**Protocol B (per-instance tuning).** Tune the hyperparameters the original authors tuned, per instance, as an upper bound on the benefit of tuning:

```bash
scripts/.venv/bin/python scripts/tune.py --solver dgcluster \
    --graphs <out_dir>/cora.csr --metric modularity --trials 50 \
    --features-suffix .feat --out params/dgcluster.cora.json
```

All included algorithms are located in the **external/** directory. Each algorithm folder contains three standardized scripts to ensure reproducibility:

* **build.sh**: Prepares the solver for testing. Typical steps include setting up a Python virtual environment, cloning specific repository versions, applying patches, and compiling binaries.
* **run.sh**: Evaluates the algorithm on a specific instance. Running the script without arguments displays a help message. Each algorithm accepts a subset of the following parameters:
    * **path_to_graph_file**: The input graph.
    * **k**: Number of repeated runs for statistical significance.
    * **timeout_seconds**: Maximum execution time.
    * **threads**: Number of CPU threads to utilize.
    * **memory_limit_gb**: Maximum memory in GB.
    * **features**: (Optional) Path to additional graph features.
* **clean.sh** Restores the directory to its original state by removing downloaded files, build artifacts, and logs.

Note that the run scripts never take the ground-truth labels file as input; instead, they check whether a file with the same name but with the **.labels** extension exists in the same location as the graph path.

Each **run.sh** script requires our evaluation script to output clustering metrics, which can be generated by running `make` in the root directory. Once the **EVAL** executable is compiled, the script outputs a single csv file for each of the **k** runs in the following format, using VieClus as an example with **k=2**:

```
algorithm, instance, run, memory, code, time   , iterations, graph         , nodes , edges  , modularity , N             , clusters, conductance, cut
vieclus  , cnr-2000,   1, 519168,    0, 3583.59,          0, cnr-2000.graph, 325557, 5477938, 0.913118487, 27400681279818,      267,  0.00302798, 0.00000006
vieclus  , cnr-2000,   2, 507164,    0, 3546.79,          0, cnr-2000.graph, 325557, 5477938, 0.913126761, 27400929563176,      281,  0.00339921, 0.00000009
```

The first seven columns always contain the following information: algorithm, instance, run number, peak memory consumption (measured in KB), return code from the algorithm, execution time, and the number of completed training iterations, which is only applicable to learning methods. The subsequent columns are results generated by our EVAL script; please refer to the last section for further details.

## File Formats

To ensure ease of testing across all solvers, we define the following file formats:

### Graph Format (METIS)

We use the **METIS** graph format for all instances. For a graph with $N$ vertices and $E$ edges:
* **Header Line**: Contains the number of vertices $N$, the number of edges $E$, and a format flag (e.g., 0 for unweighted graphs).
* **Subsequent Lines**: Line $i + 1$ lists the neighbors of vertex $i$.
* **Indices**: Vertices are 1-indexed, and edges must appear in the adjacency lists of both endpoints.

Example (3-vertex triangle, unweighted):

```
3 3 0
2 3
1 3
1 2
```

### Graph Features

Features are stored in a simple matrix format:
* **Header**: Two integers representing the number of vertices ($N$) and the number of features ($\mathcal{F}$).
* **Body**: $N$ lines, each containing $\mathcal{F}$ space-separated values.

### Clustering / Ground Truth Format

Clusterings and ground truth labels use a single-column format:
* $N$ lines in total.
* Line $i$ contains a single integer representing the cluster ID assigned to vertex $i$.

## Objective Functions

We use the Modularity ($Q$) objective function in this survey. One formulation that is easy to implement is defined as follows.

$$Q = \sum_{c \in C} \left[ \frac{L_c}{m} - \left(\frac{K_c}{2m}\right)^2 \right]$$

Where:
* $L_c$ is the number of internal edges in community $c$
* $K_c$ is the sum of degrees of nodes in community $c$
* $m$ is the number of edges in the graph

For more information on other objectives, see the dedicated [page on objective functions](docs/Objective_Functions.md).

## Solvers

| Ready | Solver | Year | AE | ML | $Q$ | F1 | WCC | ME | Link | Code |
| :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- |
| &#x2705; | CNM | 2004 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1103/PhysRevE.70.066111) | |
| &#x2705; | Walktrap | 2005 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1007/11569596_31) | |
| &#x2705; | Infomap | 2007 | &#x2705; | | | | | &#x2705; | [Link](https://doi.org/10.1073/pnas.0706851105) | [GitHub](https://github.com/mapequation/infomap) |
| &#x274C; | WT | 2007 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1145/1242572.1242805) | |
|  &#x2705; | Louvain | 2008 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1088/1742-5468/2008/10/P10008) | [SourceForge](https://sourceforge.net/projects/louvain/) |
| &#x274C; | CGGCi | 2012 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1090/conm/588/11705) | &#x274C; |
| &#x274C; | VNS | 2012 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1090/conm/588/11705) | &#x274C; |
| &#x274C; | SCD | 2014 | &#x2705; | | | &#x2705; | &#x2705; | | [Link](https://doi.org/10.1145/2566486.2568010) | &#x274C; |
| &#x2705; | COMBO | 2014 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1103/PhysRevE.90.012811) | |
| &#x274C; | ADVNDS | 2017 | &#x2705; | |  &#x2705; | | | | [Link](https://doi.org/10.1007/s10479-017-2553-9) | &#x274C; |
| &#x2705; | Hollocou | 2017 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.48550/arXiv.1712.04337) | [GitHub](https://github.com/ahollocou/graph-streaming)
| &#x2705; | VieClus | 2018 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.4230/LIPIcs.SEA.2018.3) | [GitHub](https://github.com/VieClus/VieClus) |
| &#x274C; | DANE | 2018 | | &#x2705; | | &#x2705; | | | [Link](https://doi.org/10.24963/ijcai.2018/467) | &#x274C; |
| &#x274C; | InfoFlow | 2019 | &#x2705; | | | | | &#x2705; | [Link](https://doi.org/10.3390/bdcc3030042) | [GitHub](https://github.com/felixfung/InfoFlow)
| &#x2705; | Leiden | 2019 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1038/s41598-019-41695-z) | [GitHub](https://github.com/vtraag/leidenalg) |
| &#x2705; | CommDGI | 2020 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1145/3340531.3412042) | [GitHub](https://github.com/FDUDSDE/CommDGI) |
| &#x2705; | DMoN | 2020 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://www.jmlr.org/papers/v24/20-998.html) | [GitHub](https://github.com/google-research/google-research/tree/master/graph_embedding/dmon) |
| &#x2705; | GNNS | 2022 | | &#x2705; | &#x2705; |  | | | [Link](https://doi.org/10.1007/s41109-022-00500-z) | [GitHub](https://github.com/Alexander-Belyi/GNNS) |
| &#x2705; | UCoDe | 2023 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1007/s10994-023-06402-0) | [GitHub](https://github.com/AU-DIS/UCODE) |
| &#x2705; | DGCluster | 2023 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1609/aaai.v38i10.28983) | [GitHub](https://github.com/pyrobits/DGCluster) |
| &#x2705; | MAGI | 2024 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1145/3637528.3671967) | [GitHub](https://github.com/EdisonLeeeee/MAGI) |
| &#x2705; | Bayan | 2024 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1103/PhysRevE.110.044315) | [GitHub](https://github.com/saref/bayan) |
| &#x274C; | Neuromap | 2024 | | &#x2705; | | | | &#x2705; | [Link](https://doi.org/10.52202/079017-0554) | [GitHub](https://github.com/chrisbloecker/neuromap) | 
| &#x2705; | CluStRE | 2025 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.4230/LIPIcs.SEA.2025.11) | [GitHub](https://github.com/KaHIP/CluStRE) |
| &#x2705; | LIM | 2025 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1038/s41598-025-22860-z) | [GitHub](https://github.com/wuanghoong/Less-is-More)
| &#x274C; | MaxSAT | 2024 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1007/978-3-031-97629-2_3) | &#x274C; |

## Datasets

This project references the following datasets:

* **[ADC-SBM](https://doi.org/10.48550/arXiv.2204.01376)**. Synthetically generated graphs with node features generated using the attributed, degree-corrected stochastic block model (ADC-SBM). A Python script to generate these graphs is included in the scripts directory.
* **[DIMACS](https://sites.cc.gatech.edu/dimacs10/index.shtml)**. The 32 graphs from the 10th DIMACS implementation challenge on graph clustering.
* **[Ground-Truth](https://pytorch-geometric.readthedocs.io/en/2.5.2/modules/datasets.html)**. A set of 10 commonly used graphs with ground-truth clusters. See the paper for a complete list. They can all be accessed via PyTorch Geometric.

## Evaluation Scripts

### C Evaluator (`EVAL`)

Build with `make EVAL`, then run `./EVAL <graph.metis> <pred.labels> [truth.labels]`. Each label file is interpreted line-by-line (line `i` → node `i`), and every line must contain exactly one integer cluster ID. The tool outputs a CSV row with:

1. Graph name, |V|, |E|
2. Modularity `Q`
3. The scaled numerator used to compute `Q` (useful for auditing overflow)
4. Number of non-empty clusters
5. Average conductance and cut ratio across discovered clusters (structural diagnostics that do not require ground truth)
6. If a truth file is provided: edge-level F1, edge-level accuracy, and the TP/FP/TN/FN counts used to derive them
7. Supervised set-level metrics (Adjusted Rand Index, Normalized Mutual Information, purity, inverse purity) computed directly from the per-node labels

Items 5–7 are the “non-graph structural” scores: they evaluate the clustering purely through node memberships rather than the underlying topology.

