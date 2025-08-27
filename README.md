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
| [VNS](docs/VNS.md) | 2012 | Brazil | 65 | &#x2705; | | &#x2705; | | | | [Link](https://web.archive.org/web/20170810064738id_/http://www.lix.polytechnique.fr/Labo/Leo.Liberti/dimacs10.pdf) | 
| [SCD](docs/SCD.md) | 2014 | Barcelona | 192 | &#x2705; | | | &#x2705; | &#x2705; | | [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ) |
| [Hollocou](docs/Hollocou.md) | 2017 | France | 18 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://dl.acm.org/doi/abs/10.1145/2566486.2568010?casa_token=3CTrHxKNAxkAAAAA:TkpstbQ4fAdfBbIYoKKGd2vX4tOZKE_v0zhuALljNnFivTdhtgPblkyla9ZvUTWw8XzbxDOA8Hn7JQ) | [GitHub](https://github.com/ahollocou/graph-streaming)
| [VieClus](docs/VieClus.md) | 2018 | Vienna | 14 | &#x2705; | | &#x2705; | | | | [Link](http://vieclus.taa.univie.ac.at/) | [GitHub](https://github.com/VieClus/VieClus) |
| InfoFlow | 2019 | US | 3 | &#x2705; | | | | | &#x2705; | [Link](https://www.mdpi.com/2504-2289/3/3/42) |
| CommDGI | 2018 | US | 328 | | &#x2705; | | &#x2705; | | | [Link](https://par.nsf.gov/biblio/10074625) |
| [Leiden]() | 2019 | Netherlands | 5057 | &#x2705; | | &#x2705; | | | | [Link](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/) | [GitHub](https://github.com/vtraag/leidenalg) |
| [DMoN](docs/DMoN.md) | 2020 | Germany | 438 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://www.jmlr.org/papers/v24/20-998.html) | [GitHub](https://github.com/google-research/google-research/tree/master/graph_embedding/dmon) |
| [GNNS](docs/GNNS.md) | 2022 | US | 24 | | &#x2705; | &#x2705; | | | | [Link](https://appliednetsci.springeropen.com/articles/10.1007/s41109-022-00500-z) | [GitHub](https://github.com/Alexander-Belyi/GNNS) |
| Ucode | 2023 | Denmark | 18 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://link.springer.com/article/10.1007/s10994-023-06402-0) |
| DGCluster | 2023 | US | 10 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://ojs.aaai.org/index.php/AAAI/article/view/28983) |
| [MAGI](docs/MAGI.md) | 2024 | China | 15 | | &#x2705; | &#x2705; | &#x2705; | | | [Link](https://dl.acm.org/doi/abs/10.1145/3637528.3671967) | [GitHub](https://github.com/EdisonLeeeee/MAGI) |
| Bayan | 2024 | Canada | 18 | &#x2705; | | &#x2705; | | | | [Link](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.110.044315) |
| Neuromap | 2024 | Switzerland | 3 | | &#x2705; | | | | &#x2705; | [Link](https://arxiv.org/abs/2310.01144) |
| [CluStRE](docs/CluStRE.md) | 2025 | Germany | 0 | &#x2705; | | &#x2705; | &#x2705; | | | [Link](https://arxiv.org/abs/2502.06879) | [GitHub](https://github.com/KaHIP/CluStRE) |

## Results

Graph | Vertices | Edges
:- | -: | -:
cora | 2,708 | 5,278
citeseer | 3,327 | 4,552
amazon_photo | 7,650 | 119,081
amazon_computers | 13,752 | 245,861
ogbn-arxiv | 169,343 | 1,157,799
Reddit | 232,965 | 57,307,946
ogbn-products | 2,449,029 | 61,859,012

### Cora

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.81806570 | 106 | 0.87578335 | 0.78969307
Infomap | 0.79618517 | 91 | 0.88377217 | 0.80011368
Leiden | 0.82137058 | 107 | 0.87680430 | 0.79139826
Louvain | 0.81486451 | 103 | 0.87804878 | 0.79348238
MAGI | 0.71209333 | 7 | **0.88971083** | **0.81356574**
VieClus | **0.82543311** | 105 | 0.87711864 | 0.79120879
Walktrap | 0.76456720 | 243 | 0.86007140 | 0.76979917
Truth | 0.64011881 | 7 | 1.00000000 | 1.00000000

### Citeseer

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.88853757 | 472 | 0.83223943 | 0.71924429
Infomap | 0.84518972 | 458 | 0.83702940 | 0.72231986
Leiden | 0.89123926 | 471 | 0.82407164 | 0.70650264
Louvain | 0.88879514 | 468 | 0.82726081 | 0.71045694
MAGI | 0.75119436 | 6 | **0.84647196** | **0.73901582**
VieClus | **0.89419254** | 473 | 0.83091408 | 0.71594903
Walktrap | 0.82624386 | 608 | 0.82786885 | 0.71397188
Truth | 0.53861814 | 6 | 1.00000000 | 1.00000000

### Amazon Photo

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.73179736 | 148 | **0.92487369** | **0.87051671**
Infomap | 0.56922802 | 141 | 0.90437227 | 0.82687414
Leiden | 0.73944578 | 151 | 0.92276206 | 0.86752715
Louvain | 0.73604811 | 150 | 0.92365775 | 0.86856845
MAGI | 0.70259665 | 8 | 0.92002799 | 0.86275728
VieClus | **0.74009936** | 150 | 0.92162548 | 0.86584762
Walktrap | 0.70292714 | 261 | 0.90156256 | 0.83409612
Truth | 0.63083265 | 8 | 1.00000000 | 1.00000000

### Amazon Computers

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.63424494 | 329 | 0.87011349 | 0.78927524
Infomap | 0.46438679 | 318 | **0.88374812** | 0.80024485
Leiden | 0.63905055 | 331 | 0.84362070 | 0.75696430
Louvain | 0.63512056 | 329 | 0.83208138 | 0.74150841
MAGI | 0.61149266 | 10 | 0.88032969 | **0.80417390**
VieClus | **0.64167478** | 330 | 0.83901705 | 0.75110733
Walktrap | 0.59677129 | 550 | 0.85661290 | 0.77141556
Truth | 0.47853713 | 10 | 1.00000000 | 1.00000000


### OGBN arXiv

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.68938655 | 198 | 0.76168605 | 0.65232048
Infomap | 0.63087673 | 63 | **0.79652909** | **0.68575720**
Leiden | 0.71365087 | 147 | 0.75957483 | 0.65172107
Louvain | 0.70791056 | 138 | 0.75651669 | 0.64836988
MAGI | 0.55472458 | 40 | 0.70173209 | 0.61729886
VieClus | **0.71741501** | 118 | 0.76313175 | 0.65569499
Walktrap | dnf | dnf | dnf | dnf
Truth | 0.49282546 | 40 | 1.00000000 | 1.00000000

### Reddit

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.73788497 | 26 | 0.94933688 | 0.92001233
Infomap | 0.11552535 | 4 | 0.86437954 | 0.76328098
Leiden | 0.74058835 | 27 | 0.95054146 | 0.92193309
Louvain | 0.73080958 | 24 | **0.95539124** | **0.93002834**
MAGI | 0.67979848 | 41 | 0.94902200 | 0.92436590
VieClus | **0.74165803** | 26 | 0.95213482 | 0.92456774
Walktrap | dnf | dnf | dnf | dnf
Truth | 0.70810515 | 41 | 1.00000000 | 1.00000000

### OGBN Products

Solver | Modularity | Clusters | F1 | Accuracy
:- | -: | -: | -: | -:
CluStRE | 0.87433971 | 52898 | 0.88656562 | 0.80477179
Infomap | dnf | dnf | dnf | dnf
Leiden | **0.88117325** | 52978 | **0.89003462** | **0.81057893**
Louvain | 0.87653016 | 52860 | 0.88797388 | 0.80739684
MAGI | dnf | dnf | dnf | dnf
VieClus | dnf | dnf | dnf | dnf
Walktrap | dnf | dnf | dnf | dnf
Truth | 0.72866156 | 47 | 1.00000000 | 1.00000000

## Solvers cont.

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