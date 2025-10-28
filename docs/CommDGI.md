# CommDGI (2018)

[Return to main page](../README.md)

Short recap:
* **Place** Shanghai Key Laboratory of Data Science, School of Computer Science, Fudan University, China
* **Authors** Tianqi Zhang, Yun Xiong, Jiawei Zhang, Yao Zhang, Yizhu Jiao, Yangyong Zhu
* **Type** Machine learning
* **Strategy** Community-oriented mutual information maximization. The trained model is transductive, meaning it is not ment to extend to new data. Instead, the training _is_ the clustering algorithm.
* **Cited** 74
* **Objective** Modularity, Ground Truth
* **Dataset** Cora, Citeseer and Pubmed
* Available at [Link](https://dl.acm.org/doi/abs/10.1145/3340531.3412042)

## Code

There is a github [repo](https://github.com/FDUDSDE/CommDGI) for the paper. I have made this code work for METIS inputs, but there is another level to the loss function. In the code, they only use the dgi loss, while the modularity_loss is commented out. I tried changing back to the combined loss and only modularity loss. From initial testing, the pure modularity based loss seems to work best.