import os
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

HISTORICAL_FILE = "data/processed/master_landslide_dataset.csv"
BACKGROUND_FILE = "data/processed/background_dem_features.csv"

OUTPUT_FILE = "data/processed/ml_landslide_dataset.csv"


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(HISTORICAL_FILE):
    print("ERROR: Historical dataset not found.")
    print(f"Expected: {HISTORICAL_FILE}")
    raise SystemExit


if not os.path.exists(BACKGROUND_FILE):
    print("ERROR: Background DEM dataset not found.")
    print(f"Expected: {BACKGROUND_FILE}")
    raise SystemExit


# ============================================================
# LOAD DATASETS
# ============================================================

print("=" * 60)
print("BUILDING ML LANDSLIDE DATASET")
print("=" * 60)
print()

print("Loading historical landslide dataset...")

historical = pd.read_csv(HISTORICAL_FILE)

print(
    f"Historical records: "
    f"{len(historical):,}"
)

print()

print("Loading background dataset...")

background = pd.read_csv(BACKGROUND_FILE)

print(
    f"Background records: "
    f"{len(background):,}"
)

print()


# ============================================================
# PREPARE HISTORICAL DATA
# ============================================================

print("Preparing historical records...")

# Historical records are known landslides
historical["historical_landslide"] = 1


# Keep only ML features
historical_ml = historical[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
].copy()


# ============================================================
# PREPARE BACKGROUND DATA
# ============================================================

print("Preparing background records...")

# Background records are non-landslide samples
background["historical_landslide"] = 0


# Keep only ML features
background_ml = background[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
].copy()


# ============================================================
# COMBINE DATASETS
# ============================================================

print()
print("Combining datasets...")

master = pd.concat(
    [
        historical_ml,
        background_ml
    ],
    ignore_index=True
)


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

before_duplicates = len(master)

master = master.drop_duplicates(
    subset=[
        "latitude",
        "longitude",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
).reset_index(drop=True)

after_duplicates = len(master)

duplicates_removed = (
    before_duplicates -
    after_duplicates
)


# ============================================================
# CHECK MISSING VALUES
# ============================================================

missing_values = master.isna().sum()


# ============================================================
# CHECK INVALID VALUES
# ============================================================

invalid_latitude = (
    (master["latitude"] < -90) |
    (master["latitude"] > 90)
).sum()


invalid_longitude = (
    (master["longitude"] < -180) |
    (master["longitude"] > 180)
).sum()


invalid_elevation = (
    (master["elevation_m"] < -500) |
    (master["elevation_m"] > 9000)
).sum()


invalid_slope = (
    (master["slope_degrees"] < 0) |
    (master["slope_degrees"] > 90)
).sum()


# ============================================================
# SAVE DATASET
# ============================================================

os.makedirs(
    "data/processed",
    exist_ok=True
)

master.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 60)
print("ML DATASET CREATED SUCCESSFULLY")
print("=" * 60)
print()

print(
    f"Historical records : "
    f"{len(historical_ml):,}"
)

print(
    f"Background records : "
    f"{len(background_ml):,}"
)

print(
    f"Combined records   : "
    f"{len(master):,}"
)

print(
    f"Duplicates removed : "
    f"{duplicates_removed:,}"
)

print()

print(
    f"Output file        : "
    f"{OUTPUT_FILE}"
)

print()

print("=" * 60)
print("COLUMNS")
print("=" * 60)

for column in master.columns:
    print(f"  {column}")

print()

print("=" * 60)
print("CLASS DISTRIBUTION")
print("=" * 60)

print(
    master["historical_landslide"]
    .value_counts()
    .sort_index()
)

print()

print("=" * 60)
print("MISSING VALUES")
print("=" * 60)

print(missing_values)

print()

print("=" * 60)
print("VALIDATION")
print("=" * 60)

print(
    f"Invalid latitude  : "
    f"{invalid_latitude}"
)

print(
    f"Invalid longitude : "
    f"{invalid_longitude}"
)

print(
    f"Invalid elevation : "
    f"{invalid_elevation}"
)

print(
    f"Invalid slope     : "
    f"{invalid_slope}"
)

print()

print("=" * 60)
print("SAMPLE DATA")
print("=" * 60)

print(
    master.head(10).to_string(
        index=False
    )
)

print()
print("ML dataset build completed.")