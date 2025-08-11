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

| Solver | Year | Place | #Cited | AE | ML | $Q$ | F1 | WCC | ME | Link | Code |
| :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- | :- |
| [Walktrap](docs/Walktrap.md) | 2005 | Paris | 2860 | &#x2705; | | &#x2705; | | | | [Link](https://arxiv.org/abs/physics/0512106v1) | |
| [Infomap](docs/Infomap.md) | 2007 | US | 5356 | &#x2705; | | &#x2705; | | | &#x2705; | [Link](https://www.pnas.org/doi/abs/10.1073/pnas.0706851105) | [GitHub](https://github.com/mapequation/infomap) |
| [Louvain](docs/Louvain.md) | 2008 | Belgium | 26291 | &#x2705; | | &#x2705; | | | | [Link](https://iopscience.iop.org/article/10.1088/1742-5468/2008/10/P10008/meta) | [SourceForge](https://sourceforge.net/projects/louvain/) |
| VNS | 2012 | Brazil | 65 | &#x2705; | | &#x2705; | | | | [Link](https://web.archive.org/web/20170810064738id_/http://www.lix.polytechnique.fr/Labo/Leo.Liberti/dimacs10.pdf) | 
| SCD | 2014 | Barcelona | 192 | &#x2705; | | | &#x2705; | &#x2705; | | [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ) |
| Hollocou | 2017 | France | 18 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ) |
| VieClus | 2018 | Vienna | 14 | &#x2705; | | &#x2705; | | | | [Link](http://vieclus.taa.univie.ac.at/) |
| InfoFlow | 2019 | US | 3 | &#x2705; | | | | | &#x2705; | [Link](https://www.mdpi.com/2504-2289/3/3/42) |
| CommDGI | 2018 | US | 328 | | &#x2705; | | &#x2705; | | | [Link](https://par.nsf.gov/biblio/10074625) |
| [Leiden]() | 2019 | Netherlands | 5057 | &#x2705; | | &#x2705; | | | | [Link](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/) | [GitHub](https://github.com/vtraag/leidenalg) |
| [DMoN](docs/DMoN.md) | 2020 | Germany | 438 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://www.jmlr.org/papers/v24/20-998.html) | [GitHub](https://github.com/google-research/google-research/tree/master/graph_embedding/dmon) |
| Ucode | 2023 | Denmark | 18 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://link.springer.com/article/10.1007/s10994-023-06402-0) |
| DGCluster | 2023 | US | 10 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://ojs.aaai.org/index.php/AAAI/article/view/28983) |
| [MAGI](docs/MAGI.md) | 2024 | China | 15 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://dl.acm.org/doi/abs/10.1145/3637528.3671967) | [GitHub](https://github.com/EdisonLeeeee/MAGI) |
| Bayan | 2024 | Canada | 18 | &#x2705; | | &#x2705; | | | | [Link](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.110.044315) |
| Neuromap | 2024 | Switzerland | 3 | | &#x2705; | | | | &#x2705; | [Link](https://arxiv.org/abs/2310.01144) |
| CluStRE | 2025 | Germany | 0 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://arxiv.org/abs/2502.06879) |

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