import pandas as pd

# Sample DataFrame
data = {
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "city": ["New York", "London", "Paris"]
}

df = pd.DataFrame(data)

# Save to Parquet using PyArrow
df.to_parquet("people_pyarrow.parquet", engine="pyarrow", compression="snappy")

# Save to Parquet using Fastparquet
df.to_parquet("people_fastparquet.parquet", engine="fastparquet", compression="gzip")

print("Parquet files saved successfully!")

# Read the parquet file
df_parquet = pd.read_parquet("people_pyarrow.parquet", engine="pyarrow")

print("Data from parquet:")
print(df_parquet)

# Load only specific columns
df_selected = pd.read_parquet("people_pyarrow.parquet", columns=["id", "name"])

print("Selected columns only:")
print(df_selected)

# Sample sales data
sales_data = pd.DataFrame({
    "order_id": [101, 102, 103, 104],
    "region": ["US", "EU", "US", "ASIA"],
    "amount": [250, 300, 150, 400]
})

# Save data partitioned by region
sales_data.to_parquet(
    "partitioned_sales",
    engine="pyarrow",
    partition_cols=["region"]
)

# New data
new_data = pd.DataFrame({
    "id": [4],
    "name": ["Diana"],
    "age": [28],
    "city": ["Berlin"]
})

# Append to existing file
# new_data.to_parquet("people_pyarrow.parquet", engine="pyarrow", compression="snappy", append=True)

# Existing Parquet file
file_path = "people_pyarrow.parquet"

# Load existing data
df_existing = pd.read_parquet(file_path)

# New data to append
new_data = pd.DataFrame({
    "id": [4],
    "name": ["Diana"],
    "age": [28],
    "city": ["Berlin"]
})

# Combine datasets
df_combined = pd.concat([df_existing, new_data], ignore_index=True)

# Save back to the same file
df_combined.to_parquet(file_path, engine="pyarrow", compression="snappy")

print("Data appended successfully!")

# Read the updated parquet file

import pyarrow.parquet as pq

parquet_file = pq.ParquetFile("people_pyarrow.parquet")

for batch in parquet_file.iter_batches(batch_size=2):
    df_chunk = batch.to_pandas()
    print("Processing batch:")
    print(df_chunk)
