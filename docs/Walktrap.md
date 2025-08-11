# Walktrap (2005)

Short recap:
* **Place** Laboratoire d'Informatique Algorithmique, University Paris
* **Authors** Pascal Pons, Matthieu Latapy
* **Type** Algorithm Engineering
* **Strategy** Probability distribution of short random walks, then merge communities iteratively
* **Cited** 2860
* **Objective** Modularity
* **Dataset** Various old unnamed graphs, football networks, web graphs, etc.
* Available at [Link](https://arxiv.org/abs/physics/0512106v1)

## Code

An implementation of Walktrap is included in the igraph library.

```python
import igraph as ig
g = ig.Graph.Famous("Zachary")  # e.g., Karate Club graph
wtc = g.community_walktrap(steps=4)
clusters = wtc.as_clustering()
print(clusters)              # Community membership
print(clusters.modularity)   # Modularity score of the partition
```