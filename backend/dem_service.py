
import os
import math
import rasterio


# ============================================================
# DEM DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DEM_DIR = os.path.join(
    BASE_DIR,
    "data",
    "satellite"
)


# ============================================================
# FIND HGT TILE
# ============================================================

def get_hgt_filename(latitude, longitude):

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

    lat_value = abs(lat_degree)
    lon_value = abs(lon_degree)

    filename = (
        f"{lat_prefix}{lat_value:02d}"
        f"{lon_prefix}{lon_value:03d}.hgt"
    )

    return filename


# ============================================================
# OPEN DEM TILE
# ============================================================

def open_dem(latitude, longitude):

    filename = get_hgt_filename(
        latitude,
        longitude
    )

    filepath = os.path.join(
        DEM_DIR,
        filename
    )

    if not os.path.exists(filepath):

        raise FileNotFoundError(
            f"DEM tile not found: {filename}"
        )

    return filepath


# ============================================================
# GET ELEVATION
# ============================================================

def get_elevation(latitude, longitude):

    filepath = open_dem(
        latitude,
        longitude
    )

    with rasterio.open(filepath) as dataset:

        row, col = dataset.index(
            longitude,
            latitude
        )

        elevation = dataset.read(
            1
        )[row, col]

        return float(elevation)


# ============================================================
# GET ELEVATION + SLOPE
# ============================================================

def get_terrain_features(latitude, longitude):

    filepath = open_dem(
        latitude,
        longitude
    )

    with rasterio.open(filepath) as dataset:

        # ----------------------------------------------------
        # Find pixel position
        # ----------------------------------------------------

        row, col = dataset.index(
            longitude,
            latitude
        )

        # ----------------------------------------------------
        # Read a 3 x 3 window around the selected point
        # ----------------------------------------------------

        window = rasterio.windows.Window(
            col_off=max(col - 1, 0),
            row_off=max(row - 1, 0),
            width=3,
            height=3
        )

        elevation_data = dataset.read(
            1,
            window=window
        ).astype(float)

        # ----------------------------------------------------
        # Selected elevation
        # ----------------------------------------------------

        center_row = min(1, elevation_data.shape[0] - 1)
        center_col = min(1, elevation_data.shape[1] - 1)

        elevation = elevation_data[
            center_row,
            center_col
        ]

        # ----------------------------------------------------
        # Calculate slope
        # ----------------------------------------------------

        transform = dataset.transform

        pixel_width = abs(transform.a)
        pixel_height = abs(transform.e)

        # Convert degrees to approximate meters
        meters_per_degree_lat = 111320.0

        meters_per_degree_lon = (
            111320.0 *
            math.cos(
                math.radians(latitude)
            )
        )

        cell_x = (
            pixel_width *
            meters_per_degree_lon
        )

        cell_y = (
            pixel_height *
            meters_per_degree_lat
        )

        # ----------------------------------------------------
        # Need at least a 3 x 3 window
        # ----------------------------------------------------

        if elevation_data.shape[0] < 3 or elevation_data.shape[1] < 3:

            return {
                "elevation_m": float(elevation),
                "slope_degrees": 0.0
            }

        # ----------------------------------------------------
        # Horn's slope calculation
        # ----------------------------------------------------

        z = elevation_data

        dz_dx = (
            (z[0, 2] + 2 * z[1, 2] + z[2, 2])
            -
            (z[0, 0] + 2 * z[1, 0] + z[2, 0])
        ) / (8.0 * cell_x)

        dz_dy = (
            (z[2, 0] + 2 * z[2, 1] + z[2, 2])
            -
            (z[0, 0] + 2 * z[0, 1] + z[0, 2])
        ) / (8.0 * cell_y)

        slope_radians = math.atan(
            math.sqrt(
                dz_dx ** 2 +
                dz_dy ** 2
            )
        )

        slope_degrees = math.degrees(
            slope_radians
        )

        return {
            "elevation_m": float(elevation),
            "slope_degrees": float(slope_degrees)
        }

