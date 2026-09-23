import os
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

MASTER_FILE = "data/processed/master_landslide_dataset.csv"
RAINFALL_FILE = "data/processed/event_rainfall_features.csv"

OUTPUT_FILE = "data/processed/positive_ml_features.csv"


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(MASTER_FILE):
    print("ERROR: Master landslide dataset not found.")
    print(f"Expected: {MASTER_FILE}")
    raise SystemExit

if not os.path.exists(RAINFALL_FILE):
    print("ERROR: Event rainfall dataset not found.")
    print(f"Expected: {RAINFALL_FILE}")
    raise SystemExit


# ============================================================
# LOAD DATA
# ============================================================

master = pd.read_csv(MASTER_FILE)
rainfall = pd.read_csv(RAINFALL_FILE)


print("=" * 70)
print("BUILDING POSITIVE LANDSLIDE ML FEATURES")
print("=" * 70)
print()

print(f"Master landslide records : {len(master):,}")
print(f"Rainfall records         : {len(rainfall):,}")
print()


# ============================================================
# KEEP ONLY RECORDS WITH EVENT RAINFALL
# ============================================================

rainfall = rainfall[
    [
        "sl_no",
        "latitude",
        "longitude",
        "event_date",
        "rainfall_mm_day",
        "rainfall_source"
    ]
].copy()


# ============================================================
# MERGE MASTER + RAINFALL
# ============================================================

positive = pd.merge(
    master[
        [
            "sl_no",
            "latitude",
            "longitude",
            "elevation_m",
            "slope_degrees"
        ]
    ],
    rainfall,
    on=[
        "sl_no",
        "latitude",
        "longitude"
    ],
    how="inner"
)


print(f"Matched positive records : {len(positive):,}")
print()


# ============================================================
# ADD POSITIVE CLASS LABEL
# ============================================================

positive["historical_landslide"] = 1


# ============================================================
# SELECT ML FEATURES
# ============================================================

positive = positive[
    [
        "sl_no",
        "latitude",
        "longitude",
        "event_date",
        "rainfall_mm_day",
        "elevation_m",
        "slope_degrees",
        "historical_landslide",
        "rainfall_source"
    ]
]


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before_duplicates = len(positive)

positive = positive.drop_duplicates(
    subset=[
        "latitude",
        "longitude",
        "event_date"
    ]
)

duplicates_removed = (
    before_duplicates -
    len(positive)
)


# ============================================================
# VALIDATION
# ============================================================

print("DUPLICATES")
print("-" * 70)
print(f"Duplicates removed: {duplicates_removed:,}")
print()


print("COLUMNS")
print("-" * 70)

for column in positive.columns:
    print(column)

print()


print("MISSING VALUES")
print("-" * 70)

print(
    positive.isna().sum()
)

print()


print("CLASS DISTRIBUTION")
print("-" * 70)

print(
    positive["historical_landslide"].value_counts()
)

print()


# ============================================================
# NUMERIC VALIDATION
# ============================================================

invalid_latitude = (
    (positive["latitude"] < 6) |
    (positive["latitude"] > 38)
).sum()

invalid_longitude = (
    (positive["longitude"] < 68) |
    (positive["longitude"] > 98)
).sum()

invalid_rainfall = (
    positive["rainfall_mm_day"] < 0
).sum()

invalid_elevation = (
    positive["elevation_m"] < 0
).sum()

invalid_slope = (
    (positive["slope_degrees"] < 0) |
    (positive["slope_degrees"] > 90)
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
# RAINFALL STATISTICS
# ============================================================

print("RAINFALL STATISTICS")
print("-" * 70)

print(
    positive["rainfall_mm_day"].describe()
)

print()


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

positive.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("=" * 70)
print("POSITIVE ML FEATURE DATASET CREATED")
print("=" * 70)
print()

print(f"Final records : {len(positive):,}")
print()

print("Output file:")
print(OUTPUT_FILE)

print()

print("=" * 70)
print("COMPLETED")
print("=" * 70)