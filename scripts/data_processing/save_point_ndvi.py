import os
import rasterio
import pandas as pd


# ============================================================
# TEST LOCATION
# ============================================================

latitude = 27.4728
longitude = 94.9120


# ============================================================
# FILE PATHS
# ============================================================

ndvi_file = "data/processed/ndvi_real.tiff"
output_file = "data/processed/point_ndvi.csv"


# ============================================================
# CHECK INPUT
# ============================================================

if not os.path.exists(ndvi_file):
    print("ERROR: NDVI file not found.")
    raise SystemExit


# ============================================================
# EXTRACT POINT NDVI
# ============================================================

with rasterio.open(ndvi_file) as src:

    row, col = src.index(longitude, latitude)

    if (
        row < 0
        or row >= src.height
        or col < 0
        or col >= src.width
    ):
        print("ERROR: Location is outside the NDVI raster.")
        raise SystemExit

    ndvi_value = float(src.read(1)[row, col])


# ============================================================
# CREATE DATAFRAME
# ============================================================

point_data = pd.DataFrame([
    {
        "latitude": latitude,
        "longitude": longitude,
        "ndvi": ndvi_value
    }
])


# ============================================================
# SAVE CSV
# ============================================================

os.makedirs("data/processed", exist_ok=True)

point_data.to_csv(
    output_file,
    index=False
)


# ============================================================
# DISPLAY RESULT
# ============================================================

print("Point NDVI saved successfully.")
print(f"Saved to: {output_file}")
print()
print(point_data)