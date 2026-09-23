import os
import pandas as pd

ndvi_file = "data/processed/point_ndvi.csv"
slope_file = "data/processed/point_slope.csv"
elevation_file = "data/processed/point_elevation.csv"

output_file = "data/processed/point_features.csv"

if not os.path.exists(ndvi_file):
    print("ERROR: NDVI file not found.")
    raise SystemExit

if not os.path.exists(slope_file):
    print("ERROR: Slope file not found.")
    raise SystemExit

if not os.path.exists(elevation_file):
    print("ERROR: Elevation file not found.")
    raise SystemExit

ndvi = pd.read_csv(ndvi_file)
slope = pd.read_csv(slope_file)
elevation = pd.read_csv(elevation_file)

features = pd.merge(
    ndvi,
    slope,
    on=["latitude", "longitude"]
)

features = pd.merge(
    features,
    elevation,
    on=["latitude", "longitude"]
)

features.to_csv(output_file, index=False)

print("Point feature dataset created successfully.")
print(f"Saved to: {output_file}")
print()
print(features)