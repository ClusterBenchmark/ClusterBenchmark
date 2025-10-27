# Leiden (2019)

[Return to main page](../README.md)

Short recap:
* **Place** Centre for Science and Technology Studies, Leiden University, Netherlands
* **Authors** Vincent A. Traag, Ludo Waltman, and Nees Jan van Eck
* **Type** Algorithm Engineering
* **Strategy** Improvement on Louvain, fixes issue with disconnected communities, smarter local moves
* **Cited** 5057
* **Objective** Modularity
* **Dataset** DBLP, Amazon, IMDB, Line Journal, Web of Science, Web UK
* Available at [Link](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/)

## Code

The is a pip installable python package available at [GitHub](https://github.com/vtraag/leidenalg). The official reference implementation was written in Java, and is also available at [GitHub](https://github.com/CWTSLeiden/networkanalysis).

This was exteremely slow (about 2h on the largest graph).