import os
import math
import numpy as np
import pandas as pd

INPUT_FILE = "data/historical/GSI_NER_landslide_clean.csv"
DEM_DIR = "data/satellite"
OUTPUT_FILE = "data/processed/dem_features.csv"

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# LOAD HGT TILE
# ============================================================

def load_hgt(tile_name):
    """
    Load a 1 arc-second SRTM HGT tile.
    Returns:
        elevation array
    """

    hgt_file = os.path.join(
        DEM_DIR,
        f"{tile_name}.hgt"
    )

    if not os.path.exists(hgt_file):
        raise FileNotFoundError(
            f"DEM tile not found: {hgt_file}"
        )

    # SRTM 1 arc-second tiles are normally 3601 x 3601
    data = np.fromfile(
        hgt_file,
        dtype=">i2"
    )

    expected_size = 3601 * 3601

    if len(data) != expected_size:
        raise ValueError(
            f"Unexpected HGT size for {tile_name}: "
            f"{len(data)} values"
        )

    return data.reshape(
        (3601, 3601)
    )


# ============================================================
# TILE NAME
# ============================================================

def get_tile_name(latitude, longitude):

    lat_floor = math.floor(latitude)
    lon_floor = math.floor(longitude)

    lat_prefix = "N" if lat_floor >= 0 else "S"
    lon_prefix = "E" if lon_floor >= 0 else "W"

    return (
        f"{lat_prefix}{abs(lat_floor):02d}"
        f"{lon_prefix}{abs(lon_floor):03d}"
    )


# ============================================================
# GET ELEVATION
# ============================================================

def get_elevation(data, latitude, longitude):

    lat_floor = math.floor(latitude)
    lon_floor = math.floor(longitude)

    # Convert geographic coordinate to HGT pixel position
    row = round(
        (lat_floor + 1 - latitude) * 3600
    )

    col = round(
        (longitude - lon_floor) * 3600
    )

    # Keep indices inside tile
    row = max(0, min(3600, row))
    col = max(0, min(3600, col))

    elevation = data[row, col]

    # SRTM void value
    if elevation <= -32768:
        return np.nan

    return float(elevation)


# ============================================================
# GET SLOPE
# ============================================================

def get_slope(data, latitude, longitude):

    lat_floor = math.floor(latitude)
    lon_floor = math.floor(longitude)

    row = round(
        (lat_floor + 1 - latitude) * 3600
    )

    col = round(
        (longitude - lon_floor) * 3600
    )

    # Need one pixel around the target point
    row = max(1, min(3599, row))
    col = max(1, min(3599, col))

    center = float(data[row, col])

    north = float(data[row - 1, col])
    south = float(data[row + 1, col])
    west = float(data[row, col - 1])
    east = float(data[row, col + 1])

    values = [
        center,
        north,
        south,
        west,
        east
    ]

    if any(value <= -32768 for value in values):
        return np.nan

    # Approximately 30 metres per pixel
    cell_size = 30.0

    dz_dx = (east - west) / (2 * cell_size)
    dz_dy = (south - north) / (2 * cell_size)

    slope_radians = math.atan(
        math.sqrt(
            dz_dx ** 2 +
            dz_dy ** 2
        )
    )

    slope_degrees = math.degrees(
        slope_radians
    )

    return slope_degrees


# ============================================================
# MAIN
# ============================================================

print("=" * 60)
print("DEM FEATURE EXTRACTION")
print("=" * 60)
print()

print("Reading landslide dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Records: {len(df)}")
print()

# Cache loaded tiles so the same tile is not read from disk
# thousands of times.
tile_cache = {}

elevations = []
slopes = []

failed_records = []


# ============================================================
# PROCESS RECORDS
# ============================================================

for index, row in df.iterrows():

    latitude = float(row["latitude"])
    longitude = float(row["longitude"])

    tile_name = get_tile_name(
        latitude,
        longitude
    )

    try:

        if tile_name not in tile_cache:

            print(
                f"Loading DEM tile: {tile_name}"
            )

            tile_cache[tile_name] = load_hgt(
                tile_name
            )

        dem = tile_cache[tile_name]

        elevation = get_elevation(
            dem,
            latitude,
            longitude
        )

        slope = get_slope(
            dem,
            latitude,
            longitude
        )

        elevations.append(elevation)
        slopes.append(slope)

    except Exception as error:

        print(
            f"ERROR at record {index + 1}: "
            f"{error}"
        )

        elevations.append(np.nan)
        slopes.append(np.nan)

        failed_records.append({
            "index": index + 1,
            "latitude": latitude,
            "longitude": longitude,
            "tile": tile_name,
            "error": str(error)
        })

    if (index + 1) % 500 == 0:

        print(
            f"Processed "
            f"{index + 1}/{len(df)} records"
        )


# ============================================================
# CREATE OUTPUT
# ============================================================

result = df[
    [
        "sl_no",
        "latitude",
        "longitude"
    ]
].copy()

result["elevation_m"] = elevations
result["slope_degrees"] = slopes


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("DEM FEATURE EXTRACTION SUMMARY")
print("=" * 60)
print()

print(f"Input records       : {len(df)}")
print(f"Output records      : {len(result)}")
print(
    f"Elevation available : "
    f"{result['elevation_m'].notna().sum()}"
)
print(
    f"Elevation missing   : "
    f"{result['elevation_m'].isna().sum()}"
)
print(
    f"Slope available     : "
    f"{result['slope_degrees'].notna().sum()}"
)
print(
    f"Slope missing       : "
    f"{result['slope_degrees'].isna().sum()}"
)
print(
    f"Failed records      : "
    f"{len(failed_records)}"
)

print()

if len(result) > 0:

    print("Elevation statistics:")

    print(
        result["elevation_m"].describe()
    )

    print()

    print("Slope statistics:")

    print(
        result["slope_degrees"].describe()
    )

print()

print(f"Saved to: {OUTPUT_FILE}")

print()

if failed_records:

    failed_file = (
        "data/historical/"
        "DEM_feature_extraction_failed.csv"
    )

    pd.DataFrame(
        failed_records
    ).to_csv(
        failed_file,
        index=False
    )

    print(
        f"Failed record details saved to: "
        f"{failed_file}"
    )

else:

    print(
        "All records processed successfully."
    )

print()
print("DEM feature extraction completed.")