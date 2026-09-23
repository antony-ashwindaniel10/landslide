import os
import rasterio
import matplotlib.pyplot as plt


input_file = "data/processed/ndvi_ner.tiff"


if not os.path.exists(input_file):
    print("ERROR: NER NDVI file not found.")
    raise SystemExit


with rasterio.open(input_file) as src:
    ndvi = src.read(1)
    bounds = src.bounds


plt.figure(figsize=(10, 8))

plt.imshow(
    ndvi,
    vmin=-1,
    vmax=1,
    extent=[
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top
    ]
)

plt.colorbar(label="NDVI")

plt.title("Sentinel-2 NER NDVI Map")

plt.xlabel("Longitude")

plt.ylabel("Latitude")

plt.tight_layout()

plt.show()