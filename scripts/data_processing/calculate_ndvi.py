import os
import numpy as np
import rasterio


input_file = "data/satellite/sentinel2_ner.tiff"
output_file = "data/processed/ndvi_ner.tiff"


if not os.path.exists(input_file):
    print("ERROR: Sentinel-2 image not found.")
    raise SystemExit


with rasterio.open(input_file) as src:

    red = src.read(1).astype("float32")
    nir = src.read(2).astype("float32")
    data_mask = src.read(3)

    profile = src.profile.copy()


# ---------------------------------------------------------
# Calculate NDVI
# NDVI = (NIR - Red) / (NIR + Red)
# ---------------------------------------------------------

denominator = nir + red

ndvi = np.zeros_like(red, dtype="float32")

valid_pixels = (
    (denominator != 0)
    & (data_mask == 1)
)

ndvi[valid_pixels] = (
    (nir[valid_pixels] - red[valid_pixels])
    / denominator[valid_pixels]
)


# ---------------------------------------------------------
# Save NDVI raster
# ---------------------------------------------------------

profile.update(
    count=1,
    dtype="float32"
)

os.makedirs("data/processed", exist_ok=True)


with rasterio.open(output_file, "w", **profile) as dst:
    dst.write(ndvi, 1)


# ---------------------------------------------------------
# Statistics
# ---------------------------------------------------------

valid_ndvi = ndvi[valid_pixels]


print("NER NDVI calculation completed successfully.")
print(f"Saved to: {output_file}")
print()

print("NDVI Statistics:")
print(f"Minimum: {np.min(valid_ndvi):.4f}")
print(f"Maximum: {np.max(valid_ndvi):.4f}")
print(f"Mean:    {np.mean(valid_ndvi):.4f}")
print(f"Median:  {np.median(valid_ndvi):.4f}")