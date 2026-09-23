import os
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

DEM_FILE = "data/processed/background_dem_features.csv"
RAINFALL_FILE = "data/processed/background_rainfall_features.csv"

OUTPUT_FILE = "data/processed/background_ml_features.csv"


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(DEM_FILE):
    print("ERROR: Background DEM file not found.")
    print(f"Expected: {DEM_FILE}")
    raise SystemExit

if not os.path.exists(RAINFALL_FILE):
    print("ERROR: Background rainfall file not found.")
    print(f"Expected: {RAINFALL_FILE}")
    raise SystemExit


# ============================================================
# LOAD DATA
# ============================================================

dem = pd.read_csv(DEM_FILE)
rainfall = pd.read_csv(RAINFALL_FILE)


print("=" * 70)
print("BUILDING BACKGROUND ML FEATURES")
print("=" * 70)
print()

print(f"DEM records       : {len(dem):,}")
print(f"Rainfall records  : {len(rainfall):,}")
print()


# ============================================================
# MERGE
# ============================================================

background = pd.merge(
    dem,
    rainfall,
    on=["latitude", "longitude"],
    how="inner"
)


print(f"Merged records    : {len(background):,}")
print()


# ============================================================
# ADD CLASS LABEL
# ============================================================

background["historical_landslide"] = 0


# ============================================================
# SELECT ML FEATURES
# ============================================================

background = background[
    [
        "latitude",
        "longitude",
        "event_date",
        "rainfall_mm_day",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
]


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before_duplicates = len(background)

background = background.drop_duplicates(
    subset=[
        "latitude",
        "longitude",
        "event_date"
    ]
)

duplicates_removed = before_duplicates - len(background)


# ============================================================
# VALIDATION
# ============================================================

print("DUPLICATES")
print("-" * 70)
print(f"Duplicates removed: {duplicates_removed:,}")
print()


print("COLUMNS")
print("-" * 70)

for column in background.columns:
    print(column)

print()


print("MISSING VALUES")
print("-" * 70)

print(background.isna().sum())

print()


print("CLASS DISTRIBUTION")
print("-" * 70)

print(
    background["historical_landslide"].value_counts()
)

print()


# ============================================================
# NUMERIC VALIDATION
# ============================================================

invalid_latitude = (
    (background["latitude"] < 6) |
    (background["latitude"] > 38)
).sum()

invalid_longitude = (
    (background["longitude"] < 68) |
    (background["longitude"] > 98)
).sum()

invalid_rainfall = (
    background["rainfall_mm_day"] < 0
).sum()

invalid_elevation = (
    background["elevation_m"] < 0
).sum()

invalid_slope = (
    (background["slope_degrees"] < 0) |
    (background["slope_degrees"] > 90)
).sum()


print("VALIDATION")
print("-" * 70)

print(f"Invalid latitude  : {invalid_latitude}")
print(f"Invalid longitude : {invalid_longitude}")
print(f"Invalid rainfall  : {invalid_rainfall}")
print(f"Invalid elevation : {invalid_elevation}")
print(f"Invalid slope     : {invalid_slope}")

print()


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

background.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("=" * 70)
print("BACKGROUND ML FEATURE DATASET CREATED")
print("=" * 70)
print()

print(f"Final records : {len(background):,}")
print()

print("Rainfall statistics:")
print(
    background["rainfall_mm_day"].describe()
)

print()

print("Output file:")
print(OUTPUT_FILE)

print()

print("=" * 70)
print("COMPLETED")
print("=" * 70)