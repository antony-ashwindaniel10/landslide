import pandas as pd

input_file = "data/historical/historical_landslides.csv"
output_file = "data/processed/processed_landslides.csv"

df = pd.read_csv(input_file)

df["historical_landslide"] = (
    df["historical_landslide"]
    .astype(str)
    .str.lower()
    .map({"true": 1, "false": 0})
)

df.to_csv(output_file, index=False)

print("Historical landslide data processed successfully.")
print(f"Records: {len(df)}")
print(f"Output: {output_file}")