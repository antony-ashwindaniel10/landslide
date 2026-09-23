import os
import rasterio
import numpy as np
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

ndvi_file = "data/processed/ndvi_real.tiff"
output_file = "data/processed/ndvi_summary.csv"


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(ndvi_file):
    print("ERROR: NDVI file not found.")
    raise SystemExit


# ============================================================
# READ NDVI
# ============================================================

with rasterio.open(ndvi_file) as src:
    ndvi = src.read(1)


# ============================================================
# REMOVE INVALID VALUES
# ============================================================

valid_ndvi = ndvi[np.isfinite(ndvi)]


# ============================================================
# CALCULATE STATISTICS
# ============================================================

mean_ndvi = float(np.mean(valid_ndvi))
min_ndvi = float(np.min(valid_ndvi))
max_ndvi = float(np.max(valid_ndvi))
median_ndvi = float(np.median(valid_ndvi))


# ============================================================
# CREATE SUMMARY
# ============================================================

summary = pd.DataFrame([
    {
        "mean_ndvi": mean_ndvi,
        "min_ndvi": min_ndvi,
        "max_ndvi": max_ndvi,
        "median_ndvi": median_ndvi
    }
])


# ============================================================
# SAVE
# ============================================================

os.makedirs("data/processed", exist_ok=True)

summary.to_csv(output_file, index=False)


# ============================================================
# DISPLAY
# ============================================================

print("NDVI summary created successfully.")
print(f"Saved to: {output_file}")
print()
print(summary)