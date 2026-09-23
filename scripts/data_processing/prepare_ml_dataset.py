import os
import pandas as pd

INPUT_FILE = "data/historical/GSI_NER_landslide_clean.csv"

if not os.path.exists(INPUT_FILE):
    print("ERROR: Cleaned GSI dataset not found.")
    print(f"Expected location: {INPUT_FILE}")
    raise SystemExit

print("Loading cleaned GSI NER landslide dataset...")
print()

df = pd.read_csv(INPUT_FILE)

print("=== DATASET INFORMATION ===")
print(f"Records: {len(df)}")
print(f"Columns: {len(df.columns)}")
print()

print("Columns:")
for column in df.columns:
    print(f" - {column}")

print()
print("=== DATA TYPES ===")
print(df.dtypes.to_string())

print()
print("=== ML-RELEVANT FIELDS ===")

fields = [
    "state",
    "district",
    "latitude",
    "longitude",
    "movement_type_clean",
    "event_year",
]

for field in fields:
    if field in df.columns:
        print(
            f"{field}: "
            f"available={df[field].notna().sum()}, "
            f"missing={df[field].isna().sum()}"
        )
    else:
        print(f"{field}: COLUMN NOT FOUND")

print()
print("=== COORDINATE RANGE ===")

print(f"Latitude minimum: {df['latitude'].min()}")
print(f"Latitude maximum: {df['latitude'].max()}")
print(f"Longitude minimum: {df['longitude'].min()}")
print(f"Longitude maximum: {df['longitude'].max()}")

print()
print("=== MOVEMENT TYPES ===")

print(
    df["movement_type_clean"]
    .dropna()
    .value_counts()
    .to_string()
)

print()
print("=== STATES ===")

print(
    df["state"]
    .value_counts()
    .to_string()
)

print()
print("=== EVENT YEAR RANGE ===")

known_years = df["event_year"].dropna()

if len(known_years) > 0:
    print(f"Minimum event year: {int(known_years.min())}")
    print(f"Maximum event year: {int(known_years.max())}")
else:
    print("No event years available.")

print()
print("ML dataset preparation check completed successfully.")