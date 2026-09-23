import os
import pandas as pd


# ============================================================
# FILE PATHS
# ============================================================

POSITIVE_FILE = "data/processed/positive_ml_features.csv"
BACKGROUND_FILE = "data/processed/background_ml_features.csv"

OUTPUT_FILE = "data/processed/final_ml_dataset.csv"


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(POSITIVE_FILE):
    print("ERROR: Positive ML dataset not found.")
    print(f"Expected: {POSITIVE_FILE}")
    raise SystemExit

if not os.path.exists(BACKGROUND_FILE):
    print("ERROR: Background ML dataset not found.")
    print(f"Expected: {BACKGROUND_FILE}")
    raise SystemExit


# ============================================================
# LOAD DATA
# ============================================================

positive = pd.read_csv(POSITIVE_FILE)
background = pd.read_csv(BACKGROUND_FILE)


print("=" * 70)
print("BUILDING FINAL ML DATASET")
print("=" * 70)
print()

print(f"Positive records   : {len(positive):,}")
print(f"Background records : {len(background):,}")
print()


# ============================================================
# SELECT COMMON ML FEATURES
# ============================================================

positive = positive[
    [
        "latitude",
        "longitude",
        "event_date",
        "rainfall_mm_day",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
].copy()

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
].copy()


# ============================================================
# COMBINE
# ============================================================

final = pd.concat(
    [positive, background],
    ignore_index=True
)


print(f"Combined records   : {len(final):,}")
print()


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

before = len(final)

final = final.drop_duplicates(
    subset=[
        "latitude",
        "longitude",
        "event_date",
        "rainfall_mm_day",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
)

duplicates_removed = before - len(final)


print("DUPLICATES")
print("-" * 70)
print(f"Duplicates removed : {duplicates_removed:,}")
print(f"Final records      : {len(final):,}")
print()


# ============================================================
# SHUFFLE DATA
# ============================================================

final = final.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# ============================================================
# MISSING VALUE CHECK
# ============================================================

print("MISSING VALUES")
print("-" * 70)

print(final.isna().sum())

print()


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("CLASS DISTRIBUTION")
print("-" * 70)

print(
    final["historical_landslide"].value_counts()
)

print()


# ============================================================
# FEATURE SUMMARY
# ============================================================

print("FEATURE SUMMARY")
print("-" * 70)

print(
    final[
        [
            "rainfall_mm_day",
            "elevation_m",
            "slope_degrees"
        ]
    ].describe()
)

print()


# ============================================================
# VALIDATION
# ============================================================

invalid_latitude = (
    (final["latitude"] < 6) |
    (final["latitude"] > 38)
).sum()

invalid_longitude = (
    (final["longitude"] < 68) |
    (final["longitude"] > 98)
).sum()

invalid_rainfall = (
    final["rainfall_mm_day"] < 0
).sum()

invalid_elevation = (
    final["elevation_m"] < 0
).sum()

invalid_slope = (
    (final["slope_degrees"] < 0) |
    (final["slope_degrees"] > 90)
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

final.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("=" * 70)
print("FINAL ML DATASET CREATED")
print("=" * 70)
print()

print(f"Records : {len(final):,}")
print()

print("Columns:")
for column in final.columns:
    print(f"  {column}")

print()

print("Output file:")
print(OUTPUT_FILE)

print()

print("=" * 70)
print("COMPLETED")
print("=" * 70)