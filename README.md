# From Heuristics to Graph Neural Networks: Benchmarking Modularity Maximization for Community Detection

**Authors:** Adil Chhabra, Kenneth Langedal, and Christian Schulz

## Overview

This repository contains the benchmarking harness, solver wrappers, raw experimental results, and manuscript source for **"From Heuristics to Graph Neural Networks: Benchmarking Modularity Maximization for Community Detection."**

The benchmark evaluates **17 community detection algorithms** (10 classical heuristic, streaming, memetic, and exact solvers plus 7 learning-based neural methods) alongside a feature-only $k$-means baseline across three complementary benchmarks (**Ground-Truth**, **DIMACS**, and synthetic **ADC-SBM**) under three experimental protocols:

* **Protocol A (Out-of-the-Box Standardized Comparison):** Single-threaded CPU runs with author-default hyperparameters, 1-hour wall-clock limit, and 120 GiB memory cap (5 trials per instance).
* **Protocol S (Hardware Scaling Comparison):** Multi-core CPU (32 threads) and GPU (NVIDIA RTX 4090) scaling under matched cluster budgets $k$.
* **Protocol B (Per-Instance Hyperparameter Tuning):** 50-trial Bayesian optimization with Optuna maximizing modularity $Q$ on Cora, CiteSeer, and PubMed.

## Repository Structure

```text
ClusterBenchmark/
├── data/                  # Small sample graph (Cora) for quick smoke tests
├── docs/                  # Objective functions and evaluation metrics reference
├── external/              # Per-solver wrappers (build.sh, solver.json, adapter scripts)
├── include/, src/         # C source for CONVERT (METIS -> binary CSR) and EVAL
├── Makefile               # Builds CONVERT and EVAL
├── paper/
│   ├── manuscript_natcomm.tex   # Self-contained LaTeX manuscript (Nature Communications)
│   ├── manuscript_natcomm.pdf   # Compiled manuscript PDF
│   ├── naturemag.bst            # Bibliography style
│   ├── data/                    # Processed CSVs consumed by manuscript plots
│   └── scripts/
│       └── process_results.py   # Regenerates paper/data/*.csv from results/
├── results/               # Raw JSONL benchmark logs and Protocol B tuned parameters
│   ├── protocol_a/
│   │   ├── ground_truth/        # 10 attributed Ground-Truth networks (1T CPU)
│   │   └── dimacs/              # 32 DIMACS networks (1T CPU)
│   ├── protocol_s/
│   │   ├── ground_truth/        # Matched-k 32T CPU & GPU runs on Ground-Truth
│   │   ├── ground_truth_cluster_free/  # Cluster-free (k=ceil(sqrt(n))) runs
│   │   └── dimacs/              # 32T CPU & GPU runs on DIMACS
│   ├── protocol_b/              # Optuna-tuned parameter overlays & metadata
│   └── adc_sbm/                 # Synthetic topology & feature degradation sweeps
└── scripts/               # Unified harness, instance prep, tuning, and sweep drivers
```

## Requirements

* A C compiler and `make` (builds `CONVERT` and `EVAL`).
* Python 3.12 with `venv` and `pip`.
* An **MPI** implementation (e.g., OpenMPI) — required only by the C/C++ solvers `clustre` and `vieclus`.
* *Optional:* CUDA toolkit and GPU for accelerated runs of the learning-based solvers.
* *Optional:* Academic or commercial Gurobi license for exact `bayan` runs on larger graphs.

Each solver's `external/<solver>/build.sh` provisions its own isolated environment (a dedicated Python virtual environment or compiled binary), so solvers never share conflicting dependencies.

<details>
<summary><b>No sudo?</b> Installing Python and MPI in user space</summary>

If you cannot install `python3.12-venv`, use [uv](https://docs.astral.sh/uv/) (no root needed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.12
ln -sf "$(ls -d "$(uv python dir)"/cpython-3.12*/bin/python3 | head -1)" "$HOME/.local/bin/python3"
hash -r
```

OpenMPI can also be built into `$HOME/.local`:

```bash
./configure --prefix="$HOME/.local" --disable-mpi-fortran && make -j"$(nproc)" && make install
export LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH"
```
</details>

## Setup

```bash
make                                              # builds CONVERT and EVAL
python3 -m venv scripts/.venv                     # tooling venv (instance prep + tuning)
scripts/.venv/bin/pip install numpy optuna
for d in external/*/; do [ -f "$d/build.sh" ] && bash "$d/build.sh" cpu; done   # cpu or cuda
```

`build.sh` accepts `cpu` or `cuda` for learning-based solvers (classical solvers ignore the argument).

## Preparing Instances

The harness reads a compact binary **CSR** graph (`.csr`) and, optionally, a binary feature file (`.feat`). Convert METIS `.graph` files (and sibling `.features`, if present) once:

```bash
scripts/prep_instances.sh <csr_dir> path/to/graph1.graph [graph2.graph ...]
```

Ground-truth `.labels` files are read in place and do not need to be copied.

## Running the Benchmark

Every solver is driven through `scripts/harness.py` with a uniform CLI; solver-specific invocation details and tunable parameter spaces live in `external/<solver>/solver.json`.

### Single Solver Run

```bash
python3 scripts/harness.py --solver leiden \
    --graph <csr_dir>/cora.csr --labels path/to/cora.labels \
    --runs 5 --time 3600 --memory 120 --threads 1 --device cpu \
    --out results/leiden.jsonl
```

Key options:
* `--runs`: number of repeated trials (run `i` uses deterministic seed `base + i`).
* `--time` / `--grace`: per-run wall-clock limit and hard-kill grace period (seconds).
* `--memory`: hard memory cap in GiB (enforced via cgroups when available).
* `--threads` / `--device`: CPU thread count and compute device (`cpu` or `cuda`).
* `--features`: binary `.feat` file (attached automatically for feature-consuming solvers; otherwise LDP+RNI synthetic features are generated on the fly).
* `--clusters`: cluster budget (`auto` by default).

Outputs are written as **JSON Lines (`.jsonl`)**, one record per trial, containing timing, peak RSS, iteration counts, status (`ok`, `tle`, `mle`, `error`), and `EVAL` quality metrics. Use `scripts/export_csv.py` to flatten any JSONL file into CSV.

### Protocol Drivers

* **Protocol A (1T CPU, out-of-the-box defaults):**
  ```bash
  scripts/run_protocol_a.sh <csr_dir> <labels_dir> results/protocol_a/ground_truth cpu 3600 120 5 1
  ```
* **Protocol S (32T CPU and GPU scaling):**
  ```bash
  scripts/run_scalability.sh <csr_dir> <labels_dir> results/protocol_s/ground_truth
  ```
* **Protocol B (50-trial Optuna hyperparameter tuning):**
  ```bash
  scripts/run_protocol_b_tuning.sh <csr_dir> results/protocol_b 50 "cora citeseer pubmed"
  ```
* **ADC-SBM synthetic sweeps:**
  ```bash
  scripts/.venv/bin/python scripts/run_adc_sbm_sweep.py
  ```

## Reproducing Paper Figures and Manuscript

To regenerate all processed CSV files in `paper/data/` from the raw logs in `results/`:

```bash
python3 paper/scripts/process_results.py
```

To compile the manuscript PDF (`paper/manuscript_natcomm.pdf`):

```bash
cd paper
pdflatex manuscript_natcomm.tex
bibtex manuscript_natcomm
pdflatex manuscript_natcomm.tex
pdflatex manuscript_natcomm.tex
```

## Benchmarked Solvers

| Solver | Paradigm | Year | Primary Objective | Paper | Source |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **CNM** | Classical (Agglomerative) | 2004 | Modularity | [DOI](https://doi.org/10.1103/PhysRevE.70.066111) | `igraph` |
| **Walktrap** | Classical (Random walk) | 2005 | Modularity / Walk dist. | [DOI](https://doi.org/10.1007/11569596_31) | `igraph` |
| **Infomap** | Classical (Information-theoretic) | 2008 | Map equation | [DOI](https://doi.org/10.1073/pnas.0706851105) | [GitHub](https://github.com/mapequation/infomap) |
| **Louvain** | Classical (Multilevel local move) | 2008 | Modularity | [DOI](https://doi.org/10.1088/1742-5468/2008/10/P10008) | `igraph` |
| **COMBO** | Classical (Multi-operator) | 2014 | Modularity | [DOI](https://doi.org/10.1103/PhysRevE.90.012811) | [GitHub](https://github.com/Casyfill/pyCombo) |
| **Hollocou** | Classical (Streaming) | 2017 | Modularity | [arXiv](https://arxiv.org/abs/1712.04337) | [GitHub](https://github.com/ahollocou/graph-streaming) |
| **VieClus** | Classical (Memetic / MPI) | 2018 | Modularity | [DOI](https://doi.org/10.4230/LIPIcs.SEA.2018.3) | [GitHub](https://github.com/VieClus/VieClus) |
| **Leiden** | Classical (Multilevel + refinement) | 2019 | Modularity | [DOI](https://doi.org/10.1038/s41598-019-41695-z) | [GitHub](https://github.com/vtraag/leidenalg) |
| **Bayan** | Classical (Exact ILP / B&C) | 2024 | Modularity | [DOI](https://doi.org/10.1103/PhysRevE.110.044315) | [GitHub](https://github.com/saref/bayan) |
| **CluStRE** | Classical (Streaming + refinement) | 2025 | Modularity | [DOI](https://doi.org/10.4230/LIPIcs.SEA.2025.11) | [GitHub](https://github.com/KaHIP/CluStRE) |
| **CommDGI** | Learning (Contrastive GNN) | 2020 | Infomax + Modularity | [DOI](https://doi.org/10.1145/3340531.3412042) | [GitHub](https://github.com/FDUDSDE/CommDGI) |
| **GNNS** | Learning (Recurrent GNN-inspired) | 2022 | Modularity | [DOI](https://doi.org/10.1007/s41109-022-00500-z) | [GitHub](https://github.com/Alexander-Belyi/GNNS) |
| **DMoN** | Learning (GNN pooling) | 2023 | Modularity + Collapse reg. | [JMLR](https://jmlr.org/papers/v24/20-998.html) | [GitHub](https://github.com/google-research/google-research) |
| **UCoDe** | Learning (Contrastive GNN) | 2023 | Modularity | [DOI](https://doi.org/10.1007/s10994-023-06402-0) | [GitHub](https://github.com/AU-DIS/UCODE) |
| **DGCluster** | Learning (GNN + BIRCH) | 2024 | Modularity | [DOI](https://doi.org/10.1609/aaai.v38i10.28983) | [GitHub](https://github.com/pyrobits/DGCluster) |
| **MAGI** | Learning (Contrastive GraphSAGE) | 2024 | Modularity-guided contrastive | [DOI](https://doi.org/10.1145/3637528.3671967) | [GitHub](https://github.com/EdisonLeeeee/MAGI) |
| **LIM** | Learning (Graph convolution + $k$-means) | 2025 | Modularity | [DOI](https://doi.org/10.1038/s41598-025-22860-z) | [GitHub](https://github.com/wuanghoong/Less-is-More) |

## Datasets and File Formats

* **Ground-Truth (10 graphs):** Cora, CiteSeer, PubMed, Amazon Photo, Amazon Computers, Coauthor CS, Coauthor Physics, ogbn-arxiv, Reddit, and ogbn-products (accessed via PyTorch Geometric / OGB).
* **DIMACS (32 graphs):** Standard clustering benchmark from the [10th DIMACS Implementation Challenge](https://sites.cc.gatech.edu/dimacs10/index.shtml).
* **ADC-SBM (114 synthetic graphs):** Generated via `scripts/gen_adc_sbm.py` using the [Attributed Degree-Corrected Stochastic Block Model](https://arxiv.org/abs/2204.01376).

Input source files follow simple text formats (converted to binary `.csr` / `.feat` by `scripts/prep_instances.sh`):
* **METIS `.graph`:** Header `N E 0`, followed by `N` lines of 1-indexed neighbor lists (undirected, symmetric).
* **`.features`:** Header `N F`, followed by `N` lines of `F` space-separated floats.
* **`.labels`:** `N` lines, each containing one integer cluster ID.

## Evaluation Metrics (`EVAL`)

Build with `make EVAL` and run `./EVAL <graph.metis> <pred.labels> [truth.labels]`. `EVAL` reports modularity ($Q$), its exact integer numerator $N$, cluster count, conductance, cut ratio, and (when ground-truth labels are supplied) NMI, ARI, and edge-level F1. Mathematical definitions are documented in [docs/Objective_Functions.md](docs/Objective_Functions.md).
