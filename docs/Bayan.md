# Bayan (2024)

[Return to main page](../README.md)

Short recap:
* **Place** Department of Mechanical and Industrial Engineering, University of Toronto, Canada
* **Authors** Samin Aref, Mahdi Mostajabdaveh, Hriday Chheda
* **Type** Algorithm Engineering, Exact
* **Strategy** Branch-and-cut integer programming
* **Cited** 18
* **Objective** Modularity, Ground Truth
* **Dataset** Small real networks (a few thousand edges at most)
* Available at [Link](https://doi.org/10.1103/PhysRevE.110.044315)

## Code

The code is available at [GitHub](https://github.com/saref/bayan).

Easy to install using pip install bayanpy

Issues I found:
* Needs Gurobi license...
* Does not respect the time_allowed option.
* Max 3000 edges, extremely slow at those sizes