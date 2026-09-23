import os
import rasterio
import numpy as np


input_file = "data/satellite/sentinel2_ner.tiff"


if not os.path.exists(input_file):
    print("ERROR: Sentinel-2 TIFF file not found.")
    raise SystemExit


with rasterio.open(input_file) as src:

    print("Sentinel-2 image verification")
    print("--------------------------------")
    print(f"Width: {src.width}")
    print(f"Height: {src.height}")
    print(f"Bands: {src.count}")
    print(f"CRS: {src.crs}")
    print(f"Data type: {src.dtypes}")
    print(f"Bounds: {src.bounds}")
    print()

    for band_number in range(1, src.count + 1):

        band = src.read(band_number).astype("float32")

        valid = band[np.isfinite(band)]

        print(f"Band {band_number}")
        print(f"Minimum: {np.min(valid):.6f}")
        print(f"Maximum: {np.max(valid):.6f}")
        print(f"Mean:    {np.mean(valid):.6f}")
        print(f"Median:  {np.median(valid):.6f}")
        print()

print("Verification completed.")