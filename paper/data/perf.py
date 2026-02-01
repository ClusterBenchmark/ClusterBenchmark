import pandas as pd
import argparse

def generate_performance_profile(input_csv, output_csv, x_column):
    # Load data
    df = pd.read_csv(input_csv)

    df = df.dropna(subset=[x_column])

    required_cols = {"algorithm", "instance", "run", x_column}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    # Keep only needed columns
    df = df[["algorithm", "instance", x_column]]

    # Best X per (algorithm, instance)
    best_per_alg_inst = (
        df.groupby(["algorithm", "instance"], as_index=False)
          .max()
    )

    # Compute OPT per instance
    opt_per_instance = (
        best_per_alg_inst
        .groupby("instance")[x_column]
        .max()
        .rename("OPT")
    )

    # Merge OPT back
    merged = best_per_alg_inst.merge(
        opt_per_instance,
        on="instance",
        how="left"
    )

    # Compute ratios
    merged["ratio"] = merged[x_column] / merged["OPT"]

    # Collect ratios per algorithm
    ratios_by_algorithm = {
        alg: sorted(group["ratio"].tolist(), reverse=True)
        for alg, group in merged.groupby("algorithm")
    }

    # Determine maximum number of instances solved by any algorithm
    max_len = merged["instance"].nunique()

    # Pad with zeros for missing instances
    for alg, ratios in ratios_by_algorithm.items():
        while ratios and ratios[-1] <= 0.0:
            ratios.pop()
        if len(ratios) < max_len:
            ratios_by_algorithm[alg] = ratios + [0.0] + [" "] * (max_len - (len(ratios) + 1))

    for alg, ratios in ratios_by_algorithm.items():
        ratios_by_algorithm[alg] = [1.0] + ratios

    row_count = max_len
    total_rows = row_count + 1

    profile_df = pd.DataFrame.from_dict(ratios_by_algorithm, orient="columns")
    profile_df = profile_df.reindex(range(total_rows), fill_value=0.0)

    profile_df.insert(
        0,
        "fraction",
        [i / row_count for i in range(total_rows)]
    )

    # Write CSV
    profile_df.to_csv(output_csv, index=False)

    print(f"Performance profile data written to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate performance profile data from CSV"
    )
    parser.add_argument("input_csv", help="Input CSV file")
    parser.add_argument("output_csv", help="Output CSV file")
    parser.add_argument(
        "--x_column",
        required=True,
        help="Column name to use for performance profile (lower is better)"
    )

    args = parser.parse_args()

    generate_performance_profile(
        args.input_csv,
        args.output_csv,
        args.x_column
    )
