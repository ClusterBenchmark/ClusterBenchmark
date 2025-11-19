import os
import pandas as pd

def process_folder(folder, column_x, instance_name, output="summary.csv"):
    """
    folder: path to folder with CSV files
    column_x: name of the column to extract (e.g., "latency")
    instance_name: row filter on column 'instance'
    output: output CSV filename
    """

    results = []

    # iterate through folder
    for filename in os.listdir(folder):
        if not filename.endswith(".csv"):
            continue

        filepath = os.path.join(folder, filename)
        category = os.path.splitext(filename)[0]  # remove .csv
        category = category.replace("_", r"\_")

        # read file
        df = pd.read_csv(filepath)

        # check columns exist
        if "instance" not in df.columns:
            print(f"Warning: {filename} has no 'instance' column. Skipping.")
            continue

        if column_x not in df.columns:
            print(f"Warning: {filename} has no '{column_x}' column. Skipping.")
            continue

        # filter rows where instance == instance_name
        filtered = df[df["instance"] == instance_name]

        if filtered.empty:
            print(f"Warning: {filename} contains no rows with instance={instance_name}. Skipping.")
            continue

        values = pd.to_numeric(filtered[column_x], errors="coerce").dropna()

        avg_val = values.mean()
        max_val = values.max()
        maxdiff = max_val - avg_val

        results.append({
            "category": category,
            "avg": avg_val,
            "max": max_val,
            "maxdiff": maxdiff
        })

    # write output CSV
    out_df = pd.DataFrame(results)
    out_df = out_df.sort_values(by="max", ascending=True)
    out_df.to_csv(output, index=False)
    print(f"Done! Summary written to {output}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process CSV files into avg/max summary")
    parser.add_argument("--folder", help="Folder containing CSV files")
    parser.add_argument("--column_x", help="Column name to extract values from")
    parser.add_argument("--instance_name", help="Instance name to filter rows on")
    parser.add_argument("--output", default="summary.csv", help="Output CSV file")

    args = parser.parse_args()

    process_folder(args.folder, args.column_x, args.instance_name, args.output)