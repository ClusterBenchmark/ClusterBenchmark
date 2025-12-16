# Graph Clustering Overview

This is an overview of graph clustering methods and algorithms over the last 20 or so years. The main purpose of this is not to provide a survey, but rather get a picture of what works well, and what is relevant when working on something new in this area.

## Objective Functions

The most commonly used objective function is Modularity ($Q$). One formulation that is easy to implement is defined as follows.

$$Q = \sum_{c \in C} \left[ \frac{L_c}{m} - \left(\frac{K_c}{2m}\right)^2 \right]$$

Where:
* $L_c$ is the number of internal edges in community $c$
* $K_c$ is the sum of degrees of nodes in community $c$
* $m$ is the number of edges in the graph

For more information, see the dedicated [page on objective functions](docs/Objective_Functions.md).

## Solvers

| Ready | Solver | Year | Place | #Cited | AE | ML | $Q$ | F1 | WCC | ME | Link | Code |
| :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- |
| &#x2705; | [Walktrap](docs/Walktrap.md) | 2005 | Paris | 2860 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1007/11569596_31) | |
| &#x2705; | [Infomap](docs/Infomap.md) | 2007 | US | 5356 | &#x2705; | | &#x2705; | | | &#x2705; | [Link](https://doi.org/10.1073/pnas.0706851105) | [GitHub](https://github.com/mapequation/infomap) |
|  &#x2705; | [Louvain](docs/Louvain.md) | 2008 | Belgium | 26291 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1088/1742-5468/2008/10/P10008) | [SourceForge](https://sourceforge.net/projects/louvain/) |
| &#x274C; | [VNS](docs/VNS.md) | 2012 | Brazil | 65 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1090/conm/588/11705) | &#x274C; |
| &#x274C; | [SCD](docs/SCD.md) | 2014 | Barcelona | 192 | &#x2705; | | | &#x2705; | &#x2705; | | [Link](https://doi.org/10.1145/2566486.2568010) | &#x274C; |
| &#x2705; | [Hollocou](docs/Hollocou.md) | 2017 | France | 18 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.48550/arXiv.1712.04337) | [GitHub](https://github.com/ahollocou/graph-streaming)
| &#x2705; | [VieClus](docs/VieClus.md) | 2018 | Vienna | 14 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.4230/LIPIcs.SEA.2018.3) | [GitHub](https://github.com/VieClus/VieClus) |
| &#x274C; | [DANE](docs/DANE.md) | 2018 | US | 328 | | &#x2705; | | &#x2705; | | | [Link](https://doi.org/10.24963/ijcai.2018/467) | &#x274C; |
| &#x274C; | [InfoFlow](docs/InfoFlow.md) | 2019 | US | 3 | &#x2705; | | | | | &#x2705; | [Link](https://doi.org/10.3390/bdcc3030042) | [GitHub](https://github.com/felixfung/InfoFlow)
| &#x2705; | [Leiden](docs/Leiden.md) | 2019 | Netherlands | 5057 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1038/s41598-019-41695-z) | [GitHub](https://github.com/vtraag/leidenalg) |
| &#x2705; | [CommDGI](docs/CommDGI.md) | 2020 | China | 74 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1145/3340531.3412042) | [GitHub](https://github.com/FDUDSDE/CommDGI) |
| &#x2705; | [DMoN](docs/DMoN.md) | 2020 | Germany | 438 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://www.jmlr.org/papers/v24/20-998.html) | [GitHub](https://github.com/google-research/google-research/tree/master/graph_embedding/dmon) |
| &#x2705; | [GNNS](docs/GNNS.md) | 2022 | US | 24 | | &#x2705; | &#x2705; |  | | | [Link](https://doi.org/10.1007/s41109-022-00500-z) | [GitHub](https://github.com/Alexander-Belyi/GNNS) |
| &#x2705; | [UCoDe](docs/UCoDe.md) | 2023 | Denmark | 18 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1007/s10994-023-06402-0) | [GitHub](https://github.com/AU-DIS/UCODE) |
| &#x2705; | [DGCluster](docs/DGCluster.md) | 2023 | US | 10 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1609/aaai.v38i10.28983) | [GitHub](https://github.com/pyrobits/DGCluster) |
| &#x2705; | [MAGI](docs/MAGI.md) | 2024 | China | 15 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://doi.org/10.1145/3637528.3671967) | [GitHub](https://github.com/EdisonLeeeee/MAGI) |
| &#x2705; | [Bayan](docs/Bayan.md) | 2024 | Canada | 18 | &#x2705; | | &#x2705; | | | | [Link](https://doi.org/10.1103/PhysRevE.110.044315) |
| | Neuromap | 2024 | Switzerland | 3 | | &#x2705; | | | | &#x2705; | [Link](https://arxiv.org/abs/2310.01144) |
| | [CluStRE](docs/CluStRE.md) | 2025 | Germany | 0 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://arxiv.org/abs/2502.06879) | [GitHub](https://github.com/KaHIP/CluStRE) |
| | LIM | 2025 | China | 0 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://arxiv.org/abs/2501.12946) | [GitHub](https://github.com/wuanghoong/Less-is-More)


## Papers and solvers to check out

This [paper](https://link.springer.com/article/10.1007/s13278-024-01318-6?utm_source=chatgpt.com) giving a benchmark dataset.

This [paper](https://doi.org/10.1103/PhysRevE.90.012811) on the COMBO solver.

This [paper](https://doi.org/10.1109/TCSS.2023.3306787) on the PARIS solver.

MGCCN Contrastive autoencoder

### Neuromap (2024)

* **Place** Department of Informatics, University of Zurich, Switzerland
* **Authors** Christopher Blöcker, Chester Tan, Ingo Scholtes
* **Type** Machine Learning, GNN-based
* **Strategy** Map Equation Loss
* **Cited** 3
* **Objective** Map Equation, Adjusted Mutual Informatio
* **Dataset** Cora, Citeseer, PubMed, Coauthor CS, Coauthor Phys., Cora ML, Wiki CS, ogb-arxiv
* Available at [Link](https://arxiv.org/abs/2310.01144)

### Test

* **Place** 
* **Authors** 
* **Type** 
* **Strategy** 
* **Cited** 
* **Objective** 
* **Dataset** 
* Available at [Link]()

## Datasets

This project references the following datasets:

- **[LFR Benchmark](https://github.com/eXascaleInfolab/LFR-Benchmark_UndirWeightOvp)**. Generates graphs with tunable power-law degree/community distributions; useful for validating algorithms under realistic heterogeneity. Paper [Link](https://arxiv.org/abs/0805.4770). Alternate Github [Link](https://github.com/andrealancichinetti/LFRbenchmarks).
- **[ABCD Graph Generator](https://github.com/bkamins/ABCDGraphGenerator.jl/tree/master)**. Provides fast generation of attributed, clustered benchmark graphs with configurable community size distributions. Paper [Link](https://arxiv.org/abs/2002.00843).
- **[SNAP Community Datasets](https://snap.stanford.edu/data/index.html#communities)**. Real-world networks (Amazon, DBLP, YouTube, etc.) packaged with ground-truth or heuristic community labels; several files contain overlapping memberships, so prefer the Python evaluation script described below when working with them. Paper [Link](https://arxiv.org/abs/1606.07550).

## Evaluation Scripts

### C Evaluator (`EVAL`)

Build the CLI with `make EVAL`, then run `./EVAL <graph.metis> <pred.labels> [truth.labels]`. Each label file is interpreted line-by-line (line `i` → node `i`), and every line must contain exactly one integer cluster ID. The tool outputs a CSV row with:

1. Graph name, |V|, |E|
2. Modularity `Q`
3. The scaled numerator used to compute `Q` (useful for auditing overflow)
4. Number of non-empty clusters
5. Average conductance and cut ratio across discovered clusters (structural diagnostics that do not require ground truth)
6. If a truth file is provided: edge-level F1, edge-level accuracy, and the TP/FP/TN/FN counts used to derive them
7. Supervised set-level metrics (Adjusted Rand Index, Normalized Mutual Information, purity, inverse purity) computed directly from the per-node labels

Items 5–7 are the “non-graph structural” scores: they evaluate the clustering purely through node memberships rather than the underlying topology.

### Python Evaluator (`scripts/eval_clusters.py`)

Run `python3 scripts/eval_clusters.py --pred <pred.labels> --truth <truth.labels> [--truth-multi] [--output table|json]`. Like the C tool, each line corresponds to a node; predictions must still have exactly one ID per line, but ground-truth lines may list zero or many IDs when `--truth-multi` is supplied. Under the hood:

- For single-label truth it uses scikit-learn to report ARI, AMI/NMI (geometric averaging), homogeneity/completeness/V-measure, Fowlkes–Mallows, and purity/inverse purity. These metrics match the values printed by the C evaluator (see `tests/test_eval_clusters.py`).
- For overlapping truth it switches to cdlib’s Overlapping NMI (LFK/GCE variants) plus the Omega index, and can optionally emit igraph comparison scores when `python-igraph` is installed.

Use this Python script whenever you need overlapping community support (e.g., the SNAP datasets above) or want quick JSON summaries without parsing the METIS graph. Install dependencies via `pip install scikit-learn cdlib python-igraph`.
