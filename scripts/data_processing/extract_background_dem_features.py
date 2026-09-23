import os
import math
import pandas as pd
import rasterio
from rasterio.windows import Window


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = "data/processed/background_points.csv"
OUTPUT_FILE = "data/processed/background_dem_features.csv"
DEM_FOLDER = "data/satellite"


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(INPUT_FILE):
    print("ERROR: Background points file not found.")
    print(f"Expected: {INPUT_FILE}")
    raise SystemExit

if not os.path.exists(DEM_FOLDER):
    print("ERROR: DEM folder not found.")
    print(f"Expected: {DEM_FOLDER}")
    raise SystemExit


# ============================================================
# LOAD BACKGROUND POINTS
# ============================================================

print("Loading background points...")

df = pd.read_csv(INPUT_FILE)

print(f"Background points: {len(df):,}")
print()


# ============================================================
# DEM TILE FUNCTION
# ============================================================

def get_dem_tile(latitude, longitude):

    lat_degree = math.floor(latitude)
    lon_degree = math.floor(longitude)

    if lat_degree >= 0:
        lat_prefix = "N"
    else:
        lat_prefix = "S"

    if lon_degree >= 0:
        lon_prefix = "E"
    else:
        lon_prefix = "W"

    tile_name = (
        f"{lat_prefix}{abs(lat_degree):02d}"
        f"{lon_prefix}{abs(lon_degree):03d}"
    )

    return os.path.join(
        DEM_FOLDER,
        tile_name + ".hgt"
    )


# ============================================================
# EXTRACT FEATURES
# ============================================================

elevations = []
slopes = []

failed = []

print("Extracting elevation and slope...")
print()


for index, row in df.iterrows():

    latitude = float(row["latitude"])
    longitude = float(row["longitude"])

    dem_file = get_dem_tile(
        latitude,
        longitude
    )

    try:

        if not os.path.exists(dem_file):
            raise FileNotFoundError(
                f"DEM tile not found: {dem_file}"
            )

        with rasterio.open(dem_file) as src:

            # ------------------------------------------------
            # FIND PIXEL
            # ------------------------------------------------

            raster_row, raster_col = src.index(
                longitude,
                latitude
            )

            # ------------------------------------------------
            # CHECK PIXEL BOUNDS
            # ------------------------------------------------

            if (
                raster_row < 0
                or raster_row >= src.height
                or raster_col < 0
                or raster_col >= src.width
            ):
                raise ValueError(
                    "Coordinate outside DEM bounds"
                )

            # ------------------------------------------------
            # READ CENTER ELEVATION
            # ------------------------------------------------

            center_window = Window(
                col_off=raster_col,
                row_off=raster_row,
                width=1,
                height=1
            )

            elevation_array = src.read(
                1,
                window=center_window
            )

            elevation = float(
                elevation_array[0, 0]
            )

            # ------------------------------------------------
            # READ 3x3 NEIGHBOURHOOD
            # ------------------------------------------------

            # Avoid edges of DEM tile
            if (
                raster_row <= 0
                or raster_row >= src.height - 1
                or raster_col <= 0
                or raster_col >= src.width - 1
            ):
                slope = 0.0

            else:

                neighbourhood_window = Window(
                    col_off=raster_col - 1,
                    row_off=raster_row - 1,
                    width=3,
                    height=3
                )

                window = src.read(
                    1,
                    window=neighbourhood_window
                ).astype(float)

                # ------------------------------------------------
                # 3x3 ELEVATION VALUES
                # ------------------------------------------------

                z1 = window[0, 0]
                z2 = window[0, 1]
                z3 = window[0, 2]

                z4 = window[1, 0]
                z6 = window[1, 2]

                z7 = window[2, 0]
                z8 = window[2, 1]
                z9 = window[2, 2]

                # ------------------------------------------------
                # SLOPE CALCULATION
                # ------------------------------------------------

                # SRTM HGT approximately 30 m resolution
                cell_size = 30.0

                dzdx = (
                    (z3 + 2 * z6 + z9)
                    -
                    (z1 + 2 * z4 + z7)
                ) / (8 * cell_size)

                dzdy = (
                    (z7 + 2 * z8 + z9)
                    -
                    (z1 + 2 * z2 + z3)
                ) / (8 * cell_size)

                slope_radians = math.atan(
                    math.sqrt(
                        dzdx ** 2 +
                        dzdy ** 2
                    )
                )

                slope = math.degrees(
                    slope_radians
                )

            elevations.append(elevation)
            slopes.append(slope)

    except Exception as error:

        elevations.append(None)
        slopes.append(None)

        failed.append(
            {
                "index": index,
                "latitude": latitude,
                "longitude": longitude,
                "error": str(error)
            }
        )

    if (index + 1) % 1000 == 0:

        print(
            f"Processed "
            f"{index + 1:,}/"
            f"{len(df):,}"
        )


# ============================================================
# ADD FEATURES
# ============================================================

df["elevation_m"] = elevations
df["slope_degrees"] = slopes


# ============================================================
# SAVE OUTPUT
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SAVE FAILED RECORDS
# ============================================================

FAILED_FILE = (
    "data/processed/"
    "background_dem_failed.csv"
)

if failed:

    pd.DataFrame(failed).to_csv(
        FAILED_FILE,
        index=False
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 60)
print("BACKGROUND DEM EXTRACTION COMPLETED")
print("=" * 60)

print(
    f"Records processed : {len(df):,}"
)

print(
    f"Failed records    : {len(failed):,}"
)

print(
    f"Output file       : {OUTPUT_FILE}"
)

print()

print(
    "Missing elevation:",
    df["elevation_m"].isna().sum()
)

print(
    "Missing slope:",
    df["slope_degrees"].isna().sum()
)

if df["elevation_m"].notna().any():

    print()

    print(
        "Elevation range:",
        df["elevation_m"].min(),
        "to",
        df["elevation_m"].max()
    )

    print(
        "Slope range:",
        df["slope_degrees"].min(),
        "to",
        df["slope_degrees"].max()
    )

if failed:

    print()

    print(
        f"Failed records saved to: "
        f"{FAILED_FILE}"
    )