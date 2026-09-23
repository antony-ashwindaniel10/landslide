import rasterio
import matplotlib.pyplot as plt


# ============================================================
# FILE PATH
# ============================================================

input_file = "data/processed/ndvi_real.tiff"


# ============================================================
# READ NDVI
# ============================================================

with rasterio.open(input_file) as src:
    ndvi = src.read(1)


# ============================================================
# DISPLAY NDVI MAP
# ============================================================

plt.figure(figsize=(10, 8))

plt.imshow(
    ndvi,
    vmin=-1,
    vmax=1
)

plt.colorbar(label="NDVI")

plt.title("Sentinel-2 NDVI Map")

plt.xlabel("Pixel")
plt.ylabel("Pixel")

plt.tight_layout()

plt.show()