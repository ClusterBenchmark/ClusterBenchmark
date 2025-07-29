# Graph Clustering Overview

## Objective Functions

### Modularity ($Q$)

$$Q(C) = \frac{1}{m} \sum_{C_i \in C}{(K_{C_i \rightarrow C_i} - \frac{vol(C_i)^2}{2m})}$$

Where $K_{C_i \rightarrow C_i}$ is the weight of intra-cluster edges in $C_i$, and $vol(C_i)$ is the weight of edges connected to any vertex in $C_i$.

Problem with resolution. Can be remedied somewhat by a resolution limit (resolution parameter).

### Coverage

Fraction of edges contained inside the clusters and edges containd in the graph.

$$cov(C) = \frac{m(C)}{m}$$

### Performance

Performance measures how many node pairs are grouped correctly in the clustering.

$$perf(C) = \frac{m(C)+\bar{m}(C)}{0.5n(n - 1)}$$

### Conductance

Conductance measures the bottleneck of a cut in a graph.

$$\phi(C_i) = \frac{m(C_i, V \setminus C_i)}{\min(\sum_{v \in C_i}{deg(v)}, \sum_{v \in V \setminus C_i}{deg(v)})}$$

### Inter-Cluster Conductance

$$icc(C) = 1 - \max_{C_i \in C} \phi(C_i)$$

### Weighted Community Detection (WCC)

The weighted community detection metric is based on the fact that real networks contain a large number of triangles due to their community structure.

$$WCC(x, C) = \frac{t(x, C)}{t(x,V)} * \frac{vt(x,V)}{|C \setminus \{x\}| + vt(x, V \setminus C)}$$

(when $t(x, V) = 0$, $WCC(x, C) = 0$).

Where $t(x, C)$ is the number of triangles that $x$ closes with the vertices in $C$, and $vt(x, C)$ is the number of vertices in $C$ that closes at least one triangle with $x$ and another vertex in $V$.

$$WCC(C_i) = \frac{1}{|C_i|} \sum_{x \in C_i}{WCC(x, C_i)}$$

And finally

$$WCC(C) = \frac{1}{|V|} \sum_{C_i \in C}{(|C_i|*WCC(C_i))}$$

### Map Equation (ME)

The formal definition uses some non-standard notation. But it can essentially be described as minimizing the expected description length (using Huffman coding-like principles) of the random walk.

$$L(C) = q_\curvearrowright H(\mathcal{Q}) + \sum_{C_i \in C}{p^i_\circlearrowleft H(C_i)}$$

Where $q_\curvearrowright$ is the probability that the walk exits a cluster, $H(\mathcal{Q})$ is the entropy of the codebook for clusters (low if a random walk mostly stays in few clusters), $p^i_\circlearrowleft$ is the probability that the walk is inside cluster $i$, and $H(C_i)$ is the entropy of the codebook for nodes within cluster $i$.

## Solvers

| Solver | Year | Place | #Cited | AE | ML | $Q$ | F1 | WCC | ME | Link |
| :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- |
| Walktrap | 2005 | Paris | 2860 | &#x2705; | | &#x2705; | | | | [Link](https://arxiv.org/abs/physics/0512106v1) |
| Infomap | 2007 | US | 5356 | &#x2705; | | &#x2705; | | | &#x2705; | [Link](https://www.pnas.org/doi/abs/10.1073/pnas.0706851105) |
| Louvain | 2008 | Belgium | 26291 | &#x2705; | | &#x2705; | | | | [Link](https://iopscience.iop.org/article/10.1088/1742-5468/2008/10/P10008/meta) |
| VNS | 2012 | Brazil | 65 | &#x2705; | | &#x2705; | | | | [Link](https://web.archive.org/web/20170810064738id_/http://www.lix.polytechnique.fr/Labo/Leo.Liberti/dimacs10.pdf) |
| SCD | 2014 | Barcelona | 192 | &#x2705; | | | &#x2705; | &#x2705; | | [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ) |
| Hollocou | 2017 | France | 18 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ) |
| VieClus | 2018 | Vienna | 14 | &#x2705; | | &#x2705; | | | | [Link](http://vieclus.taa.univie.ac.at/) |
| InfoFlow | 2019 | US | 3 | &#x2705; | | | | | &#x2705; | [Link](https://www.mdpi.com/2504-2289/3/3/42) |
| CommDGI | 2018 | US | 328 | | &#x2705; | | &#x2705; | | | [Link](https://par.nsf.gov/biblio/10074625) |
| Leiden | 2019 | Netherlands | 5057 | &#x2705; | | &#x2705; | | | | [Link](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/) |
| DMoN | 2020 | Germany | 438 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://www.jmlr.org/papers/v24/20-998.html) |
| Ucode | 2023 | Denmark | 18 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://link.springer.com/article/10.1007/s10994-023-06402-0) |
| DGCluster | 2023 | US | 10 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://ojs.aaai.org/index.php/AAAI/article/view/28983) |
| MAGI | 2024 | China | 15 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://dl.acm.org/doi/abs/10.1145/3637528.3671967) |
| Bayan | 2024 | Canada | 18 | &#x2705; | | &#x2705; | | | | [Link](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.110.044315) |
| Neuromap | 2024 | Switzerland | 3 | | &#x2705; | | | | &#x2705; | [Link](https://arxiv.org/abs/2310.01144) |
| CluStRE | 2025 | Germany | 0 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://arxiv.org/abs/2502.06879) |

### Walktrap (2005)

* **Place** Laboratoire d'Informatique Algorithmique, University Paris
* **Authors** Pascal Pons, Matthieu Latapy
* **Type** Algorithm Engineering
* **Strategy** Probability distribution of short random walks, then merge communities iteratively
* **Cited** 2860
* **Objective** Modularity
* **Dataset** Various old unnamed graphs, football networks, web graphs, etc.
* Available at [Link](https://arxiv.org/abs/physics/0512106v1)

### Infomap (2007)

* **Place** Department of Biology, University of Washington, US
* **Authors** Martin Rosvall, Carl T. Bergstrom
* **Type** Algorithm Engineering
* **Strategy** Random walks (encodes the paths)
* **Cited** 5356
* **Objective** Map Equation, Modularity
* **Dataset** Single instance, journal citation network (directed and weighted)
* Available at [Link](https://www.pnas.org/doi/abs/10.1073/pnas.0706851105)

### Louvain (2008)

* **Place** Department of Mathematical Engineering, Universié Catholique de Louvain, Belgium
* **Authors** Vincent D Blondel, Jean-Loup Guillaume,
Renaud Lambiotte, Etienne Lefebvre1
* **Type** Algorithm Engineering
* **Strategy** Local moving nodes, and aggregate the network
* **Cited** 26291
* **Objective** Modularity
* **Dataset** Karate , Arxive, Internet, Web nd.edu, Phone, Web uk-2005, WebBase 2001
* Available at [Link](https://iopscience.iop.org/article/10.1088/1742-5468/2008/10/P10008/meta)

### VNS (2012)

* **Place** Dept. of Computer Engineering and Automation, Universidade Federal do Rio Grande do Norte, Brazil
* **Authors** Daniel Aloise, Gilles Caporossi, Pierre Hansen, Leo Liberti, Sylvain Perron, Manuel Ruiz
* **Type** Algorithm Engineering
* **Strategy** Variable neighborhood search
* **Cited** 65
* **Objective** Modularity
* **Dataset** 10th DIMACS
* Available at [Link](https://web.archive.org/web/20170810064738id_/http://www.lix.polytechnique.fr/Labo/Leo.Liberti/dimacs10.pdf)

### SCD (2014)

* **Place** Universitat Politècnica de Catalunya (UPC), Barcelona
* **Authors** Arnau Prat-Pérez, David Dominguez-Sal, Josep-LLuis Larriba-Pey
* **Type** Algorithm Engineering, Parallel
* **Strategy** Build clusters around nodes with many triangles, then iterative refinement
* **Cited** 192
* **Objective** WCC (triangle counting), Ground Truth
* **Dataset** Amazon, DBLP, YT, LiveJ., Orkut, and Friend
* Available at [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ)

### Hollocou (2017)

* **Place** National Institute for Research in Digital Science and Technology, France
* **Authors** Alexandre Hollocou, Julien Maudet, Thomas Bonald, Marc Lelarge
* **Type** Algorithm Engineering, Streaming
* **Strategy** Single pass edge streaming, compare degrees of its endpoints
* **Cited** 18
* **Objective** Modularity, Ground Truth
* **Dataset** Amazon, DBLP, YT, LiveJ., Orkut, and Friend
* Available at [Link](https://arxiv.org/abs/1712.04337)

### VieClus (2018)

* **Place** University of Vienna
* **Authors** Sonja Biedermann, Monika Henzinger, Christian Schulz, Bernhard Schuster
* **Type** Algorithm Engineering
* **Strategy** Memetic multi-level scheme with local search
* **Cited** 14
* **Objective** Modularity
* **Dataset** 10th DIMACS instances
* Available at [Link](http://vieclus.taa.univie.ac.at/)

### InfoFlow (2019)

* **Place** Department of Ophthalmology, State University of New York, US
* **Authors** Park K. Fung
* **Type** Algorithm Engineering
* **Strategy** Greedy community merging
* **Cited** 3
* **Objective** Map Equation
* **Dataset** Large real world graphs (no details beyond size)
* Available at [Link](https://www.mdpi.com/2504-2289/3/3/42)

### Leiden (2019)

* **Place** Centre for Science and Technology Studies, Leiden University, Netherlands
* **Authors** Vincent A. Traag, Ludo Waltman, and Nees Jan van Eck
* **Type** Algorithm Engineering
* **Strategy** Improvement on Louvain, fixes issue with disconnected communities, smarter local moves
* **Cited** 5057
* **Objective** Modularity
* **Dataset** DBLP, Amazon, IMDB, Line Journal, Web of Science, Web UK
* Available at [Link](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/)

### CommDGI (2018)

* **Place** Department of Electrical and Computer Engineering
University of Pittsburgh, US
* **Authors** Hongchang Gao, Heng Huang
* **Type** Machine learning
* **Strategy** Node embeddings using community-preserving regularization
* **Cited** 328
* **Objective** Ground Truth
* **Dataset** Cora, Citeseer, PubMed, Coauthor CS, Coauthor Phys.
* Available at [Link](https://par.nsf.gov/biblio/10074625)

### DMoN (2020)

* **Place** Google Research and TU Dortmund, Germany
* **Authors** Anton Tsitsulin, John Palowitch, Bryan Perozzi, Emmanuel Müller
* **Type** Machine learning, GNN-based
* **Strategy** Optimize a spectral relaxation of modularity
* **Cited** 438
* **Objective** Modularity, Ground Truth
* **Dataset** Cora, Citeseer, PubMed, Coauthor CS, Coauthor Phys.
* Available at [Link](https://www.jmlr.org/papers/v24/20-998.html)

### Ucode (2023)

* **Place** Department of Computer Science, Aarhus University, Denmark
* **Authors** Atefeh Moradan, Andrew Draganov, Davide Mottin, Ira Assent
* **Type** Machine Learning, GNN-based
* **Strategy** Contrastive modularity loss 
* **Cited** 18
* **Objective** Modularity, Ground Truth
* **Dataset** Cora, Citeseer, PubMed, Coauthor CS, Coauthor Phys.
* Available at [Link](https://link.springer.com/article/10.1007/s10994-023-06402-0)

### DGCluster (2023)

* **Place** University of California, Santa Barbara, US
* **Authors** Aritra Bhowmick, Mert Kosan, Zexi Huang, Ambuj Singh, Sourav Medya 
* **Type** Machine Learning, GNN-based
* **Strategy** Contrastive learning
* **Cited** 10
* **Objective** Modularity, Ground Truth
* **Dataset** Cora, Citeseer, Amazon Photo, Amazon Computers, Reddit, ogbn-arxiv, ogbn-products, ogbn‑papers100M
* Available at [Link](https://ojs.aaai.org/index.php/AAAI/article/view/28983)

### MAGI (2024) 

* **Place** Ant Group (Chinese financial technology company)
* **Authors** Yunfei Liu + 11 others
* **Type** Machine Learning, GNN-based
* **Strategy** Contrastive learning
* **Cited** 15
* **Objective** Modularity, Ground Truth
* **Dataset** Cora, Citeseer, Amazon Photo, Amazon Computers, Reddit, ogbn-arxiv, ogbn-products, ogbn‑papers100M
* Available at [Link](https://dl.acm.org/doi/abs/10.1145/3637528.3671967)


### Bayan (2024)

* **Place** Department of Mechanical and Industrial Engineering, University of Toronto, Canada
* **Authors** Samin Aref, Mahdi Mostajabdaveh, Hriday Chheda
* **Type** Algorithm Engineering, Exact
* **Strategy** Branch-and-cut integer programming
* **Cited** 18
* **Objective** Modularity, Ground Truth
* **Dataset** Small real networks (a few thousand edges at most)
* Available at [Link](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.110.044315)

### Neuromap (2024)

* **Place** Department of Informatics, University of Zurich, Switzerland
* **Authors** Christopher Blöcker, Chester Tan, Ingo Scholtes
* **Type** Machine Learning, GNN-based
* **Strategy** Map Equation Loss
* **Cited** 3
* **Objective** Map Equation, Adjusted Mutual Informatio
* **Dataset** Cora, Citeseer, PubMed, Coauthor CS, Coauthor Phys., Cora ML, Wiki CS, ogb-arxiv
* Available at [Link](https://arxiv.org/abs/2310.01144)

### CluStRE (2025)

* **Place** Heidelberg University
* **Authors** Adil Chhabra, Shai Dorian Peretz, Christian Schulz
* **Type** Algorithm Engineering, Streaming
* **Strategy** On-the-fly construction of a dynamic quotient graph and re-streaming with local search
* **Cited** 0
* **Objective** Modularity, Ground Truth
* **Dataset** SNAP, 10th DIMACS, Cora, Citeseer, AmazonCP, and PubMed
* Available at [Link](https://arxiv.org/abs/2502.06879)

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