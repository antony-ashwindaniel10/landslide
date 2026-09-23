import os
import rasterio

latitude = 27.4728
longitude = 94.9120

input_file = "data/satellite/dem_test.tif"

if not os.path.exists(input_file):
    print("ERROR: DEM file not found.")
    raise SystemExit

with rasterio.open(input_file) as src:

    row, col = src.index(longitude, latitude)

    if (
        row < 0
        or row >= src.height
        or col < 0
        or col >= src.width
    ):
        print("ERROR: Test location is outside the DEM image.")
        raise SystemExit

    elevation_value = float(src.read(1)[row, col])

print("Point elevation extraction completed successfully.")
print()
print(f"Latitude:   {latitude}")
print(f"Longitude:  {longitude}")
print(f"Raster row: {row}")
print(f"Raster col: {col}")
print(f"Elevation:  {elevation_value:.2f} metres")