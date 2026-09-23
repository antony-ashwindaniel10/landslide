import os
import pandas as pd

historical_file = "data/historical/historical_landslides.csv"
point_features_file = "data/processed/point_features.csv"
output_file = "data/processed/master_landslide_dataset.csv"

if not os.path.exists(historical_file):
    print("ERROR: Historical dataset not found.")
    raise SystemExit

if not os.path.exists(point_features_file):
    print("ERROR: Point feature dataset not found.")
    raise SystemExit

historical = pd.read_csv(historical_file)
point_features = pd.read_csv(point_features_file)

master = pd.merge(
    historical,
    point_features,
    on=["latitude", "longitude"],
    how="left"
)

master = master[
    [
        "latitude",
        "longitude",
        "rainfall",
        "soil_moisture",
        "slope_degrees",
        "elevation_m",
        "ndvi",
        "historical_landslide"
    ]
]

master.to_csv(output_file, index=False)

print("Master landslide dataset created successfully.")
print(f"Saved to: {output_file}")
print()
print(master)