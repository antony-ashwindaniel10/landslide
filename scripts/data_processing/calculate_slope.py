import os
import numpy as np
import rasterio

input_file = "data/satellite/dem_test.tif"
output_file = "data/processed/slope_real.tif"

if not os.path.exists(input_file):
    print("ERROR: DEM file not found.")
    raise SystemExit

with rasterio.open(input_file) as src:
    elevation = src.read(1).astype("float32")
    profile = src.profile.copy()
    transform = src.transform

# Find the approximate latitude of the DEM
latitude = transform.f

# Convert geographic pixel size to metres
meters_per_degree_lat = 111320.0
meters_per_degree_lon = 111320.0 * np.cos(np.radians(latitude))

pixel_width_m = abs(transform.a) * meters_per_degree_lon
pixel_height_m = abs(transform.e) * meters_per_degree_lat

# Calculate elevation change between neighbouring pixels
gradient_y, gradient_x = np.gradient(
    elevation,
    pixel_height_m,
    pixel_width_m
)

# Calculate slope in degrees
slope = np.degrees(
    np.arctan(
        np.sqrt(
            gradient_x ** 2 +
            gradient_y ** 2
        )
    )
)

# Prepare output GeoTIFF
profile.update(
    dtype="float32",
    count=1,
    nodata=-9999
)

os.makedirs("data/processed", exist_ok=True)

# Save slope raster
with rasterio.open(output_file, "w", **profile) as dst:
    dst.write(slope.astype("float32"), 1)

print("Slope calculation completed successfully.")
print(f"Saved to: {output_file}")
print()
print("Slope statistics:")
print(f"Minimum: {np.nanmin(slope):.2f} degrees")
print(f"Maximum: {np.nanmax(slope):.2f} degrees")
print(f"Mean:    {np.nanmean(slope):.2f} degrees")
print(f"Median:  {np.nanmedian(slope):.2f} degrees")