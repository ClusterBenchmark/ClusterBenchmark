import pandas as pd
from pathlib import Path

# --- Configuration ---
input_folder = 'assortativity'  # Change to your folder path
target_column = 'nmi'             # Change to the column you want to extract
output_file = 'combined.csv'
# ---------------------

all_data = []
first=0

# Iterate through all CSV files in the folder
for file_path in Path(input_folder).glob("*.csv"):
    try:

        if first == 0:
            # Load only the specific column
            df = pd.read_csv(file_path, usecols=["instance", target_column])
            first = 1
        else:
            df = pd.read_csv(file_path, usecols=[target_column])
        
        # Get filename without .csv (using .stem)
        clean_filename = file_path.stem
        
        # Rename the column to match the filename
        df = df.rename(columns={target_column: clean_filename})
        
        all_data.append(df)
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")

# Combine all dataframes side-by-side
if all_data:
    combined_df = pd.concat(all_data, axis=1)
    combined_df.to_csv(output_file, index=False)
    print(f"Done! Combined data saved to {output_file}")
else:
    print("No valid CSV files found.")
