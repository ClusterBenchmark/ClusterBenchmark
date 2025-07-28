# Graph Clustering Overview

## Objective functions

### Modularity

$Q(C) = \frac{1}{m} \sum_{C_i \in C}{(K_{C_i \rightarrow C_i} - \frac{vol(C_i)^2}{2m})}$

Where $K_{C_i \rightarrow C_i}$ is the weight of intra-cluster edges in $C_i$, and $vol(C_i)$ is the weight of edges connected to any vertex in $C_i$.

### Coverage

### Performance

### Conductance

### Map Equation

The formal definition uses very non-standard notation. But it can essentially be described as minimizing the expected description length (using Huffman coding-like principles) of the random walk.

### Weighted Community Detection (WCC)

Community metric based on the fact that real networks contain a large number of triangles due to their community structure.

$WCC(x, C) = \frac{t(x, C)}{t(x,V)} * \frac{vt(x,V)}{|C \setminus \{x\}| + vt(x, V \setminus C)}$

(when $t(x, V) = 0$, $WCC(x, C) = 0$).

Where $t(x, C)$ is the number of triangles that $x$ closes with the vertices in $C$, and $vt(x, C)$ is the number of vertices in $C$ that closes at least one triangle with $x$ and another vertex in $V$.

$WCC(C_i) = \frac{1}{|C_i|} \sum_{x \in C_i}{WCC(x, C_i)}$

And finally

$WCC(C) = \frac{1}{|V|} \sum_{C_i \in C}{(|C_i|*WCC(C_i))}$

## Solvers

### VieClus (2018)

* Adil, Shai, and Christian
* Modularity
* Memetic Clustering

### CluStRE (2025)

* Adil, Shai, and Christian
* Modularity
* Ground truth on Cora, Citeseer, AmazonCP, and PubMed
* Streaming

### Hollocou (2017)

* Alexandre Hollocou, Julien Maudet, Thomas Bonald, and Marc Lelarge
* Modularity
* Ground truth on Amazon, DBLP, YT, LiveJ., Orkut, and Friend.
* Streaming

### SCD (2014)

* Arnau Prat-Pérez, David Dominguez-Sal, and Josep-LLuis Larriba-Pey
* WCC
* Parallel (focus on scalability)
* Triangle counting

### Walktrap

### OSLOM

### CGGC

### VNS

### Louvain

* Two phases: (1) local moving nodes, and (2) aggregate the network
*  Modularity

### Leiden (2019)

* V. A. Traag, L. Waltman, and N. J. van Eck
* Improvement on Louvain, fixes issue with disconnected communities
* Smarter local moves
* Modularity

### Infomap (2007)

* M. Rosvall, C. T. Bergstrom
* Random walks (encodes the paths)
* Map Equation and Modularity
* Directed edges

### MAGI (2024) 

* Machine learning

### DGCluster (2023) 

* Machine learning
* Modularity
* Supports node features (but why?)

### Bayan (2022)

* Exact
* Modularity

## Datasets