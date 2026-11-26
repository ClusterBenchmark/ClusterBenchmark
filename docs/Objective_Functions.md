# Objective Functions and Evaluation Metrics

This document summarizes the objective functions and partition-quality metrics used in the benchmark and companion manuscript. [Return to README](../README.md).

## Modularity ($Q$)

Modularity measures the fraction of edges falling within communities minus the expected fraction under a degree-preserving random null model:

$$Q(\mathcal{C}) = \sum_{c \in \mathcal{C}} \left[ \frac{L_c}{m} - \left(\frac{K_c}{2m}\right)^2 \right]$$

where:
* $L_c$ is the number of undirected internal edges with both endpoints in community $c$,
* $K_c = \sum_{v \in c} \deg(v)$ is the sum of vertex degrees in community $c$,
* $m = |E|$ is the total number of undirected edges in the graph.

For numerically stable evaluation in C (`EVAL`), multiplying $Q$ by $4m^2$ yields an exact integer numerator:

$$N = 4m \sum_{c \in \mathcal{C}} L_c - \sum_{c \in \mathcal{C}} K_c^2, \qquad Q(\mathcal{C}) = \frac{N}{4m^2}.$$

## Ground-Truth Recovery Metrics

When reference node labels $\mathcal{T}$ are available (as in the **Ground-Truth** and **ADC-SBM** benchmarks), predicted partitions $\mathcal{C}$ are evaluated against $\mathcal{T}$ using two standard set-level metrics:

### Normalized Mutual Information (NMI)

NMI measures how much information the predicted clustering $\mathcal{C}$ shares with the ground-truth partition $\mathcal{T}$, normalized by their average Shannon entropy:

$$\operatorname{NMI}(\mathcal{C}, \mathcal{T}) = \frac{2\, I(\mathcal{C}; \mathcal{T})}{H(\mathcal{C}) + H(\mathcal{T})}$$

where $H(\cdot)$ is the Shannon entropy of a partition's cluster-size distribution and $I(\mathcal{C}; \mathcal{T})$ is their mutual information. NMI lies in $[0, 1]$, where $1$ denotes an exact match and $0$ denotes statistical independence.

### Adjusted Rand Index (ARI)

ARI counts all unordered node pairs that are grouped consistently by $\mathcal{C}$ and $\mathcal{T}$ (either placed together in both partitions or separated in both) and corrects the resulting agreement rate for chance:

$$\operatorname{ARI}(\mathcal{C}, \mathcal{T}) = \frac{\operatorname{RI}(\mathcal{C}, \mathcal{T}) - \mathbb{E}[\operatorname{RI}]}{1 - \mathbb{E}[\operatorname{RI}]}$$

where $\operatorname{RI}$ is the raw Rand Index and $\mathbb{E}[\operatorname{RI}]$ is its expectation under random partitions with the same cluster sizes. ARI equals $1$ for an exact match and has an expected value of $0$ for independent random clusterings (and can take small negative values when agreement falls below chance).

## Structural Diagnostics

In addition to modularity, `EVAL` reports two topology-based structural diagnostics:

* **Conductance** of a cluster $c$:
  $$\phi(c) = \frac{m(c, V \setminus c)}{\min\!\left(\operatorname{vol}(c),\; \operatorname{vol}(V \setminus c)\right)}$$
  where $m(c, V \setminus c)$ is the number of edges crossing the boundary of $c$ and $\operatorname{vol}(c) = \sum_{v \in c} \deg(v)$. Lower values indicate more well-separated clusters.
* **Coverage**: the fraction of graph edges contained inside clusters, $\operatorname{cov}(\mathcal{C}) = \frac{1}{m} \sum_{c \in \mathcal{C}} L_c$.

## Alternative Objectives Used by Benchmarked Solvers

While modularity is the primary unsupervised objective in this benchmark, two classical solvers optimize related community objectives:

* **Map Equation** (**Infomap**): minimizes the expected description length $L(\mathcal{C}) = q_\curvearrowright H(\mathcal{Q}) + \sum_{c \in \mathcal{C}} p^c_\circlearrowleft H(\mathcal{P}^c)$ of a random walk using a two-level Huffman codebook, where $q_\curvearrowright$ is the inter-cluster transition probability and $p^c_\circlearrowleft$ is the stay-plus-exit probability for cluster $c$.
* **Random-Walk Distance** (**Walktrap**): performs hierarchical agglomerative clustering using a Ward-style distance between short-length random-walk transition distributions, selecting the dendrogram cut that maximizes modularity $Q$.
