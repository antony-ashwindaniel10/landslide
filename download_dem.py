import os
import math
import gzip
import shutil
import requests
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BACKGROUND_FILE = "data/processed/background_points.csv"
OUTPUT_DIR = "data/satellite"

BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"


# Create satellite directory if it does not exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FUNCTION: GET DEM TILE NAME
# ============================================================

def get_tile_name(latitude, longitude):
    """
    Convert latitude and longitude into SRTM HGT tile name.

    Examples:

    27.03, 94.93  -> N27E094
    28.50, 97.20  -> N28E097
    24.27, 92.50  -> N24E092
    """

    lat_floor = math.floor(latitude)
    lon_floor = math.floor(longitude)

    # Latitude prefix
    if lat_floor >= 0:
        lat_prefix = "N"
    else:
        lat_prefix = "S"

    # Longitude prefix
    if lon_floor >= 0:
        lon_prefix = "E"
    else:
        lon_prefix = "W"

    lat_number = abs(lat_floor)
    lon_number = abs(lon_floor)

    tile_name = (
        f"{lat_prefix}{lat_number:02d}"
        f"{lon_prefix}{lon_number:03d}"
    )

    return tile_name


# ============================================================
# START
# ============================================================

print("=" * 60)
print("DOWNLOADING REQUIRED DEM TILES")
print("=" * 60)
print()


# ============================================================
# CHECK BACKGROUND FILE
# ============================================================

if not os.path.exists(BACKGROUND_FILE):

    print("ERROR: Background points file not found.")
    print()
    print(f"Expected file:")
    print(BACKGROUND_FILE)

    raise SystemExit


# ============================================================
# LOAD BACKGROUND POINTS
# ============================================================

print("Loading background points...")

df = pd.read_csv(BACKGROUND_FILE)

print(f"Background points: {len(df):,}")
print()


# ============================================================
# FIND REQUIRED DEM TILES
# ============================================================

required_tiles = set()


for _, row in df.iterrows():

    latitude = float(row["latitude"])
    longitude = float(row["longitude"])

    tile_name = get_tile_name(
        latitude,
        longitude
    )

    required_tiles.add(tile_name)


# Sort tiles for easier reading
required_tiles = sorted(required_tiles)


# ============================================================
# DISPLAY REQUIRED TILES
# ============================================================

print("=" * 60)
print("DEM TILE REQUIREMENT")
print("=" * 60)
print()

print(
    f"Unique DEM tiles required: "
    f"{len(required_tiles)}"
)

print()

for tile in required_tiles:
    print(f"  {tile}")

print()


# ============================================================
# DOWNLOAD STATUS LISTS
# ============================================================

downloaded = []
already_exists = []
failed = []


# ============================================================
# PROCESS EACH TILE
# ============================================================

for index, tile_name in enumerate(
    required_tiles,
    start=1
):

    print("=" * 60)

    print(
        f"Processing tile "
        f"{index}/{len(required_tiles)}: "
        f"{tile_name}"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # GET LATITUDE BAND
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # N28E093 -> N28
    # N29E095 -> N29
    #
    # The N/S prefix MUST be included.
    #
    # --------------------------------------------------------

    latitude_band = tile_name[:3]


    # --------------------------------------------------------
    # FILE PATHS
    # --------------------------------------------------------

    hgt_file = os.path.join(
        OUTPUT_DIR,
        f"{tile_name}.hgt"
    )

    gz_file = os.path.join(
        OUTPUT_DIR,
        f"{tile_name}.hgt.gz"
    )


    # --------------------------------------------------------
    # CHECK EXISTING HGT FILE
    # --------------------------------------------------------

    if os.path.exists(hgt_file):

        print("HGT file already exists.")
        print(f"Skipping: {hgt_file}")

        already_exists.append(tile_name)

        continue


    # --------------------------------------------------------
    # CHECK EXISTING COMPRESSED FILE
    # --------------------------------------------------------

    if os.path.exists(gz_file):

        print(
            "Compressed HGT file already exists."
        )

        print("Extracting...")

        try:

            with gzip.open(
                gz_file,
                "rb"
            ) as source:

                with open(
                    hgt_file,
                    "wb"
                ) as target:

                    shutil.copyfileobj(
                        source,
                        target
                    )


            # Remove compressed file
            os.remove(gz_file)

            print(
                "Extraction successful."
            )

            print(
                f"Created: {hgt_file}"
            )

            downloaded.append(tile_name)

            continue


        except Exception as error:

            print(
                f"Extraction failed: {error}"
            )

            # Remove damaged files
            if os.path.exists(gz_file):
                os.remove(gz_file)

            if os.path.exists(hgt_file):
                os.remove(hgt_file)


    # --------------------------------------------------------
    # BUILD DOWNLOAD URL
    # --------------------------------------------------------

    url = (
        f"{BASE_URL}/"
        f"{latitude_band}/"
        f"{tile_name}.hgt.gz"
    )


    print()
    print("Downloading:")
    print(url)
    print()


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            stream=True,
            timeout=(30, 180)
        )


        print(
            f"HTTP status: "
            f"{response.status_code}"
        )


        response.raise_for_status()


        # ----------------------------------------------------
        # SAVE COMPRESSED FILE
        # ----------------------------------------------------

        total_size = 0


        with open(
            gz_file,
            "wb"
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:

                    file.write(chunk)

                    total_size += len(chunk)


        print(
            f"Downloaded size: "
            f"{total_size:,} bytes"
        )


        # ----------------------------------------------------
        # EXTRACT HGT
        # ----------------------------------------------------

        print(
            "Extracting HGT file..."
        )


        with gzip.open(
            gz_file,
            "rb"
        ) as source:

            with open(
                hgt_file,
                "wb"
            ) as target:

                shutil.copyfileobj(
                    source,
                    target
                )


        # ----------------------------------------------------
        # REMOVE COMPRESSED FILE
        # ----------------------------------------------------

        os.remove(gz_file)


        print(
            "Extraction successful."
        )

        print(
            f"Saved: {hgt_file}"
        )


        downloaded.append(tile_name)


    except Exception as error:

        print()
        print(
            f"DOWNLOAD FAILED: {error}"
        )


        failed.append(tile_name)


        # ----------------------------------------------------
        # REMOVE INCOMPLETE FILES
        # ----------------------------------------------------

        if os.path.exists(gz_file):

            os.remove(gz_file)


        if os.path.exists(hgt_file):

            os.remove(hgt_file)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("DEM DOWNLOAD SUMMARY")
print("=" * 60)
print()


print(
    f"Tiles required  : "
    f"{len(required_tiles)}"
)

print(
    f"Downloaded      : "
    f"{len(downloaded)}"
)

print(
    f"Already existed : "
    f"{len(already_exists)}"
)

print(
    f"Failed          : "
    f"{len(failed)}"
)

print()


# ============================================================
# DOWNLOADED LIST
# ============================================================

if downloaded:

    print("Downloaded:")

    for tile in downloaded:

        print(
            f"  {tile}"
        )

    print()


# ============================================================
# EXISTING LIST
# ============================================================

if already_exists:

    print("Already existed:")

    for tile in already_exists:

        print(
            f"  {tile}"
        )

    print()


# ============================================================
# FAILED LIST
# ============================================================

if failed:

    print("FAILED:")

    for tile in failed:

        print(
            f"  {tile}"
        )

    print()

    print(
        "Some DEM tiles are still missing."
    )

else:

    print(
        "ALL REQUIRED DEM TILES ARE AVAILABLE."
    )


print()
print(
    "DEM download process completed."
)