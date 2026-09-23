import os
import random
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


# ============================================================
# FILE PATHS
# ============================================================

BOUNDARY_FILE = "data/boundaries/NER_states.geojson"
LANDSLIDE_FILE = "data/historical/GSI_NER_landslide_clean.csv"
OUTPUT_FILE = "data/processed/background_points.csv"


# ============================================================
# SETTINGS
# ============================================================

# Generate approximately the same number of background points
# as historical landslide points.
RANDOM_SEED = 42


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(BOUNDARY_FILE):
    print("ERROR: NER boundary file not found.")
    print(f"Expected: {BOUNDARY_FILE}")
    raise SystemExit

if not os.path.exists(LANDSLIDE_FILE):
    print("ERROR: Landslide dataset not found.")
    print(f"Expected: {LANDSLIDE_FILE}")
    raise SystemExit


# ============================================================
# LOAD DATA
# ============================================================

print("Loading NER state boundaries...")
states = gpd.read_file(BOUNDARY_FILE)

print("Loading historical landslide dataset...")
landslides = pd.read_csv(LANDSLIDE_FILE)

print(f"Historical landslide records: {len(landslides):,}")
print()


# ============================================================
# PREPARE LANDSLIDE COORDINATES
# ============================================================

landslide_coordinates = set(
    zip(
        landslides["latitude"].round(6),
        landslides["longitude"].round(6)
    )
)

print(
    f"Known landslide coordinates: "
    f"{len(landslide_coordinates):,}"
)


# ============================================================
# MERGE STATE GEOMETRIES
# ============================================================

ner_geometry = states.geometry.union_all()

minx, miny, maxx, maxy = ner_geometry.bounds

print()
print("NER boundary bounds:")
print(f"Minimum longitude: {minx}")
print(f"Minimum latitude : {miny}")
print(f"Maximum longitude: {maxx}")
print(f"Maximum latitude : {maxy}")
print()


# ============================================================
# RANDOM POINT GENERATION
# ============================================================

random.seed(RANDOM_SEED)

target_points = len(landslides)

background_points = []

attempts = 0
max_attempts = target_points * 100

print("Generating background points...")
print()


while len(background_points) < target_points:

    attempts += 1

    if attempts > max_attempts:
        print()
        print("ERROR: Could not generate enough background points.")
        print(f"Generated: {len(background_points):,}")
        print(f"Required : {target_points:,}")
        raise SystemExit

    # Random longitude
    longitude = random.uniform(minx, maxx)

    # Random latitude
    latitude = random.uniform(miny, maxy)

    point = Point(longitude, latitude)

    # Must be inside NER boundary
    if not ner_geometry.contains(point):
        continue

    # Round for comparison
    coordinate_key = (
        round(latitude, 6),
        round(longitude, 6)
    )

    # Do not generate a point exactly on a known landslide location
    if coordinate_key in landslide_coordinates:
        continue

    # Avoid duplicate background points
    if coordinate_key in background_points:
        continue

    background_points.append(coordinate_key)

    if len(background_points) % 1000 == 0:
        print(
            f"Generated "
            f"{len(background_points):,}/"
            f"{target_points:,}"
        )


# ============================================================
# CREATE DATAFRAME
# ============================================================

background_df = pd.DataFrame(
    background_points,
    columns=["latitude", "longitude"]
)


# ============================================================
# ADD LABEL
# ============================================================

background_df["historical_landslide"] = 0


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

background_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("=" * 55)
print("BACKGROUND POINT GENERATION COMPLETED")
print("=" * 55)

print(f"Background points : {len(background_df):,}")
print(f"Historical points : {len(landslides):,}")
print(f"Random seed       : {RANDOM_SEED}")
print(f"Saved to          : {OUTPUT_FILE}")

print()
print("Label distribution:")
print(background_df["historical_landslide"].value_counts())

print()
print("Sample:")
print(background_df.head())