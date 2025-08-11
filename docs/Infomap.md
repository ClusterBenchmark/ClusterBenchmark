# Infomap (2007)

Short recap:
* **Place** Department of Biology, University of Washington, US
* **Authors** Martin Rosvall, Carl T. Bergstrom
* **Type** Algorithm Engineering
* **Strategy** Random walks (encodes the paths)
* **Cited** 5356
* **Objective** Map Equation, Modularity
* **Dataset** Single instance, journal citation network (directed and weighted)
* Available at [Link](https://www.pnas.org/doi/abs/10.1073/pnas.0706851105)

## Code

There is a [GitHub](https://github.com/mapequation/infomap) repository for the project.

```python
pip install infomap
```

```python
import pandas as pd
from infomap import Infomap

# Load and deduplicate edges
df = pd.read_csv("edges.csv")
df['edge'] = df.apply(lambda row: tuple(sorted((row['source'], row['target']))), axis=1)
edges = df['edge'].drop_duplicates().tolist()

# Create and run Infomap
im = Infomap("--undirected")  # or use "--directed" if applicable

for u, v in edges:
    im.add_link(u, v)

im.run()

# Print the communities
for node in im.nodes:
    print(f"Node {node.node_id} → Module {node.module_id}")
```