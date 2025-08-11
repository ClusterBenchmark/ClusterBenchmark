# Objective Functions

Here is a list of commonly used objective functions used for graph clustering.

## Modularity ($Q$)

$$Q(C) = \frac{1}{m} \sum_{C_i \in C}{(K_{C_i \rightarrow C_i} - \frac{vol(C_i)^2}{2m})}$$

Where $K_{C_i \rightarrow C_i}$ is the weight of intra-cluster edges in $C_i$, and $vol(C_i)$ is the weight of edges connected to any vertex in $C_i$.

Problem with resolution. Can be remedied somewhat by a resolution limit (resolution parameter).

## Coverage

Fraction of edges contained inside the clusters and edges containd in the graph.

$$cov(C) = \frac{m(C)}{m}$$

## Performance

Performance measures how many node pairs are grouped correctly in the clustering.

$$perf(C) = \frac{m(C)+\bar{m}(C)}{0.5n(n - 1)}$$

## Conductance

Conductance measures the bottleneck of a cut in a graph.

$$\phi(C_i) = \frac{m(C_i, V \setminus C_i)}{\min(\sum_{v \in C_i}{deg(v)}, \sum_{v \in V \setminus C_i}{deg(v)})}$$

## Inter-Cluster Conductance

$$icc(C) = 1 - \max_{C_i \in C} \phi(C_i)$$

## Weighted Community Detection (WCC)

The weighted community detection metric is based on the fact that real networks contain a large number of triangles due to their community structure.

$$WCC(x, C) = \frac{t(x, C)}{t(x,V)} * \frac{vt(x,V)}{|C \setminus \{x\}| + vt(x, V \setminus C)}$$

(when $t(x, V) = 0$, $WCC(x, C) = 0$).

Where $t(x, C)$ is the number of triangles that $x$ closes with the vertices in $C$, and $vt(x, C)$ is the number of vertices in $C$ that closes at least one triangle with $x$ and another vertex in $V$.

$$WCC(C_i) = \frac{1}{|C_i|} \sum_{x \in C_i}{WCC(x, C_i)}$$

And finally

$$WCC(C) = \frac{1}{|V|} \sum_{C_i \in C}{(|C_i|*WCC(C_i))}$$

## Map Equation (ME)

The formal definition uses some non-standard notation. But it can essentially be described as minimizing the expected description length (using Huffman coding-like principles) of the random walk.

$$L(C) = q_\curvearrowright H(\mathcal{Q}) + \sum_{C_i \in C}{p^i_\circlearrowleft H(C_i)}$$

Where $q_\curvearrowright$ is the probability that the walk exits a cluster, $H(\mathcal{Q})$ is the entropy of the codebook for clusters (low if a random walk mostly stays in few clusters), $p^i_\circlearrowleft$ is the probability that the walk is inside cluster $i$, and $H(C_i)$ is the entropy of the codebook for nodes within cluster $i$.