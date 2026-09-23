import os
import rasterio


# ============================================================
# TEST LOCATION
# ============================================================

latitude = 27.4728
longitude = 94.9120


# ============================================================
# INPUT FILE
# ============================================================

input_file = "data/processed/ndvi_real.tiff"


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(input_file):
    print("ERROR: NDVI file not found.")
    raise SystemExit


# ============================================================
# READ NDVI RASTER
# ============================================================

with rasterio.open(input_file) as src:

    # Convert geographic coordinates to raster row/column
    row, col = src.index(longitude, latitude)

    # Check whether point is inside raster
    if (
        row < 0
        or row >= src.height
        or col < 0
        or col >= src.width
    ):
        print("ERROR: Test location is outside the NDVI image.")
        raise SystemExit

    # Read NDVI value at the location
    ndvi_value = float(src.read(1)[row, col])


# ============================================================
# DISPLAY RESULT
# ============================================================

print("Point NDVI extraction completed successfully.")
print()
print(f"Latitude:  {latitude}")
print(f"Longitude: {longitude}")
print(f"Raster row: {row}")
print(f"Raster col: {col}")
print(f"NDVI:       {ndvi_value:.4f}")