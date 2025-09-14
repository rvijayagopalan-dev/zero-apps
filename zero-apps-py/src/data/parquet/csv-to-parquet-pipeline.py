import pandas as pd

import os

print("Current working directory:", os.getcwd())

# Sample data

# Step 1: Load CSV
transactions_df = pd.read_csv("transactions.csv")

# Step 2: Convert to Parquet with partitioning
transactions_df.to_parquet(
    "transactions_parquet",
    engine="pyarrow",
    compression="snappy",
    partition_cols=["region"]
)

# Step 3: Read only required columns
subset_df = pd.read_parquet("transactions_parquet", columns=["transaction_id", "price"])

print(subset_df.head())
print("CSV to Parquet conversion completed successfully!")