import os
import pandas as pd


historical_file = "data/historical/historical_landslides.csv"
features_file = "data/processed/all_point_features.csv"

output_file = "data/processed/master_landslide_dataset.csv"


# ---------------------------------------------------------
# Check files
# ---------------------------------------------------------

if not os.path.exists(historical_file):
    print(f"ERROR: File not found: {historical_file}")
    raise SystemExit

if not os.path.exists(features_file):
    print(f"ERROR: File not found: {features_file}")
    raise SystemExit


# ---------------------------------------------------------
# Load datasets
# ---------------------------------------------------------

historical = pd.read_csv(historical_file)
features = pd.read_csv(features_file)


# ---------------------------------------------------------
# Merge using latitude and longitude
# ---------------------------------------------------------

master = pd.merge(
    historical,
    features,
    on=["latitude", "longitude"],
    how="left"
)


# ---------------------------------------------------------
# Remove duplicate columns if present
# ---------------------------------------------------------

columns_to_remove = []

for column in master.columns:

    if column.endswith("_x") or column.endswith("_y"):
        columns_to_remove.append(column)

if columns_to_remove:
    print("Removing duplicate columns:")
    print(columns_to_remove)

    master = master.drop(
        columns=columns_to_remove
    )


# ---------------------------------------------------------
# Save master dataset
# ---------------------------------------------------------

os.makedirs("data/processed", exist_ok=True)

master.to_csv(
    output_file,
    index=False
)


# ---------------------------------------------------------
# Display result
# ---------------------------------------------------------

print()
print("Master landslide dataset created successfully.")
print(f"Saved to: {output_file}")
print()

print("Dataset shape:")
print(master.shape)

print()

print("Master dataset:")
print(master)

print()

print("Missing values:")
print(master.isnull().sum())