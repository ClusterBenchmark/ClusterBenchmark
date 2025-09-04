import pandas as pd
import glob
import os
import sys
import numpy as np

# Adjust to your folder
folder = sys.argv[1]
column = sys.argv[2]

files = glob.glob(os.path.join(folder, "*.csv"))

merged = []

for f in files:
    df = pd.read_csv(f)  # expects co   lumns: x,y
    # Pivot to make rows (x) become columns
    row = df.set_index("graph")[column].to_dict()
    
    # Add filename (without extension) as the "solver" column
    row["solver"] = os.path.splitext(os.path.basename(f))[0]
    merged.append(row)

# Combine into a single DataFrame, aligning on row labels
out = pd.DataFrame(merged)

out = out.fillna("DNF")

# Reorder columns: name first, then all the x-values
cols = ["solver"] + [c for c in out.columns if c != "solver"]
out = out[cols]

# Save
out.to_csv("merged.csv", index=False)

rename_cols = {
    "cora.graph" : "Cora",
    "citeseer.graph" : "Citeseer",
    "amazon_photo.graph" : "Amazon-Photo",
    "amazon_computers.graph" : "Amazon-Computers",
    "ogbn-arxiv.graph" : "OGBN-Arxiv",
    "Reddit.graph" : "Reddit",
    "ogbn-products.graph" : "OGBN-Products"
}

rename_entries = {
    "walktrap" : "Walktrap",
    "clustre_strong" : "CluStRE-Strong",
    "clustre_light" : "CluStRE-Light",
    "leiden" : "Leiden",
    "louvain" : "Louvain",
    "hollocou" : "Hollocou",
    "infoflow" : "InfoFlow",
    "infomap" : "InfoMap",
    "dcore" : "D-Core",
    "magi" : "MAGI",
    "ground_truth" : "Ground-Truth",
    "vieclus" : "VieClus"
}

# Columns with numeric data (skip 'name')
num_cols = [c for c in out.columns if c != "solver"]

# Convert 'DNF' to NaN for numeric processing
# df_num = out.replace("DNF", np.nan).infer_objects(copy=False).copy()
df_num = out.apply(lambda col: pd.to_numeric(col, errors="coerce") if col.name != "solver" else col)

col_max = df_num[num_cols].astype(float).max()

# Round numbers to 4 decimals, bold the maxima
def format_entry(val, col):
    if pd.isna(val):
        return "DNF"
    val_rounded = f"{val:.4f}"
    if np.isclose(val, col_max[col], rtol=1e-9):
        return f"\\textbf{{{val_rounded}}}"
    return val_rounded

# Loop over all numeric columns (skip 'name')
for col in out.columns[1:]:
    out[col] = df_num[col].apply(lambda x: format_entry(x, col))

out = out.rename(columns=rename_cols)
out = out.replace(rename_entries)

# Save
out.to_csv(column + ".csv", index=False)