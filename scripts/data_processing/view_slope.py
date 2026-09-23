import rasterio
import matplotlib.pyplot as plt

input_file = "data/processed/slope_real.tif"

with rasterio.open(input_file) as src:
    slope = src.read(1)

plt.figure(figsize=(10, 8))

plt.imshow(slope, vmin=0, vmax=60)

plt.colorbar(label="Slope (degrees)")

plt.title("DEM-Derived Slope Map")

plt.xlabel("Pixel")
plt.ylabel("Pixel")

plt.tight_layout()
plt.show()