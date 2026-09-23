import os
import rasterio
import pandas as pd


historical_file = "data/historical/historical_landslides.csv"

ndvi_file = "data/processed/ndvi_ner.tiff"
slope_file = "data/processed/slope_real.tif"
dem_file = "data/satellite/dem_test.tif"

output_file = "data/processed/all_point_features.csv"


# ---------------------------------------------------------
# Check files
# ---------------------------------------------------------

for file in [
    historical_file,
    ndvi_file,
    slope_file,
    dem_file
]:
    if not os.path.exists(file):
        print(f"ERROR: File not found: {file}")
        raise SystemExit


# ---------------------------------------------------------
# Load historical locations
# ---------------------------------------------------------

locations = pd.read_csv(historical_file)

results = []


# ---------------------------------------------------------
# Open raster datasets
# ---------------------------------------------------------

with rasterio.open(ndvi_file) as ndvi_src, \
     rasterio.open(slope_file) as slope_src, \
     rasterio.open(dem_file) as dem_src:

    for _, point in locations.iterrows():

        latitude = point["latitude"]
        longitude = point["longitude"]


        # -------------------------------------------------
        # NDVI
        # -------------------------------------------------

        ndvi_row, ndvi_col = ndvi_src.index(
            longitude,
            latitude
        )

        if (
            0 <= ndvi_row < ndvi_src.height
            and 0 <= ndvi_col < ndvi_src.width
        ):

            ndvi_value = float(
                ndvi_src.read(1)[ndvi_row, ndvi_col]
            )

        else:

            ndvi_value = None


        # -------------------------------------------------
        # Slope
        # -------------------------------------------------

        slope_row, slope_col = slope_src.index(
            longitude,
            latitude
        )

        if (
            0 <= slope_row < slope_src.height
            and 0 <= slope_col < slope_src.width
        ):

            slope_value = float(
                slope_src.read(1)[slope_row, slope_col]
            )

        else:

            slope_value = None


        # -------------------------------------------------
        # Elevation
        # -------------------------------------------------

        dem_row, dem_col = dem_src.index(
            longitude,
            latitude
        )

        if (
            0 <= dem_row < dem_src.height
            and 0 <= dem_col < dem_src.width
        ):

            elevation_value = float(
                dem_src.read(1)[dem_row, dem_col]
            )

        else:

            elevation_value = None


        results.append({
            "latitude": latitude,
            "longitude": longitude,
            "ndvi": ndvi_value,
            "slope_degrees": slope_value,
            "elevation_m": elevation_value
        })


# ---------------------------------------------------------
# Create output dataframe
# ---------------------------------------------------------

features = pd.DataFrame(results)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

os.makedirs("data/processed", exist_ok=True)

features.to_csv(
    output_file,
    index=False
)


print("All point features extracted successfully.")
print(f"Saved to: {output_file}")
print()

print(features)