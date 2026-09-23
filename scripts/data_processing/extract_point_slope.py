import os
import rasterio

latitude = 27.4728
longitude = 94.9120

input_file = "data/processed/slope_real.tif"

if not os.path.exists(input_file):
    print("ERROR: Slope file not found.")
    raise SystemExit

with rasterio.open(input_file) as src:

    row, col = src.index(longitude, latitude)

    if (
        row < 0
        or row >= src.height
        or col < 0
        or col >= src.width
    ):
        print("ERROR: Test location is outside the slope image.")
        raise SystemExit

    slope_value = float(src.read(1)[row, col])

print("Point slope extraction completed successfully.")
print()
print(f"Latitude:  {latitude}")
print(f"Longitude: {longitude}")
print(f"Raster row: {row}")
print(f"Raster col: {col}")
print(f"Slope:      {slope_value:.2f} degrees")