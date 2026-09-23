import os
import rasterio
import pandas as pd

latitude = 27.4728
longitude = 94.9120

input_file = "data/satellite/dem_test.tif"
output_file = "data/processed/point_elevation.csv"

if not os.path.exists(input_file):
    print("ERROR: DEM file not found.")
    raise SystemExit

with rasterio.open(input_file) as src:

    row, col = src.index(longitude, latitude)

    elevation_value = float(src.read(1)[row, col])

data = pd.DataFrame([
    {
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation_value
    }
])

data.to_csv(output_file, index=False)

print("Point elevation saved successfully.")
print(f"Saved to: {output_file}")
print()
print(data)