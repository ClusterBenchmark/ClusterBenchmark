# MAGI (2024) 

[Return to main page](../README.md)

Short recap:
* **Place** Ant Group (Chinese financial technology company)
* **Authors** Yunfei Liu + 11 others
* **Type** Machine Learning, GNN-based
* **Strategy** Contrastive learning
* **Cited** 15
* **Objective** Modularity, Ground Truth
* **Dataset** Cora, Citeseer, Amazon Photo, Amazon Computers, Reddit, ogbn-arxiv, ogbn-products, ogbn‑papers100M
* Available at [Link](https://dl.acm.org/doi/abs/10.1145/3637528.3671967)

## Code

There is a [GitHub](https://github.com/EdisonLeeeee/MAGI) repository for the project.

I had a hard time making the `pip install -r requirements.txt` command work, but manually installing the dependencies using pip worked in the end.

## Further Info

MAGI is not really a clustering algorithm. Instead, it performs graph embedding and then runs k-means clustering. This means the user needs to know the number of clusters upfront. They also train one model for each instance, so in a sense, the training is the algorithm. It is not intended to train a model that can then be reused. It makes some sense given the unsupervised nature (modularity based relaxation). But one downside of this is that the whole procedure is extremely slow. 