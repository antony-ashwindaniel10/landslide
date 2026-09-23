import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

POSITIVE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "positive_ml_features_v2.csv"
)

BACKGROUND_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "background_ml_features_v2.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_ml_dataset_v2.csv"
)


# ============================================================
# START
# ============================================================

print("=" * 70)
print("BUILDING FINAL ML DATASET V2")
print("=" * 70)


# ============================================================
# LOAD POSITIVE DATA
# ============================================================

print("\nLoading positive landslide data...")

positive = pd.read_csv(POSITIVE_FILE)

print("Positive records:", len(positive))


# ============================================================
# LOAD BACKGROUND DATA
# ============================================================

print("\nLoading background data...")

background = pd.read_csv(BACKGROUND_FILE)

print("Background records:", len(background))


# ============================================================
# ADD CLASS LABELS
# ============================================================

positive["historical_landslide"] = 1
background["historical_landslide"] = 0


# ============================================================
# SELECT COMMON FEATURES
# ============================================================

feature_columns = [
    "latitude",
    "longitude",
    "event_date",
    "rainfall_mm_day",
    "elevation_m",
    "slope_degrees",
    "soil_wetness_gwet_top",
    "soil_moisture_source",
    "historical_landslide"
]


print("\nChecking required columns...")

for col in feature_columns:
    if col not in positive.columns:
        raise ValueError(
            f"Missing column in positive dataset: {col}"
        )

    if col not in background.columns:
        raise ValueError(
            f"Missing column in background dataset: {col}"
        )

print("All required columns found.")


# ============================================================
# KEEP ONLY REQUIRED COLUMNS
# ============================================================

positive = positive[feature_columns].copy()
background = background[feature_columns].copy()


# ============================================================
# COMBINE DATASETS
# ============================================================

print("\nCombining positive + background datasets...")

final_df = pd.concat(
    [positive, background],
    ignore_index=True
)

print("Combined records:", len(final_df))


# ============================================================
# CONVERT DATE
# ============================================================

final_df["event_date"] = pd.to_datetime(
    final_df["event_date"],
    errors="coerce"
)


# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "latitude",
    "longitude",
    "rainfall_mm_day",
    "elevation_m",
    "slope_degrees",
    "soil_wetness_gwet_top",
    "historical_landslide"
]

for col in numeric_columns:
    final_df[col] = pd.to_numeric(
        final_df[col],
        errors="coerce"
    )


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

before_duplicates = len(final_df)

final_df = final_df.drop_duplicates(
    subset=[
        "latitude",
        "longitude",
        "event_date",
        "historical_landslide"
    ]
).copy()

duplicates_removed = (
    before_duplicates - len(final_df)
)

print("Duplicate records removed:", duplicates_removed)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("DATASET VALIDATION")
print("=" * 70)


# Missing values

print("\nMissing values:")

print(
    final_df[feature_columns].isna().sum()
)


# Class distribution

print("\nClass distribution:")

print(
    final_df["historical_landslide"]
    .value_counts()
    .sort_index()
)


# Source distribution

print("\nSoil moisture source distribution:")

print(
    final_df["soil_moisture_source"]
    .value_counts(dropna=False)
)


# ============================================================
# FEATURE STATISTICS
# ============================================================

print("\n" + "=" * 70)
print("FEATURE STATISTICS")
print("=" * 70)


print("\nRainfall:")
print(
    "Minimum :",
    round(final_df["rainfall_mm_day"].min(), 4)
)
print(
    "Maximum :",
    round(final_df["rainfall_mm_day"].max(), 4)
)
print(
    "Mean    :",
    round(final_df["rainfall_mm_day"].mean(), 4)
)


print("\nSoil wetness:")
print(
    "Minimum :",
    round(final_df["soil_wetness_gwet_top"].min(), 4)
)
print(
    "Maximum :",
    round(final_df["soil_wetness_gwet_top"].max(), 4)
)
print(
    "Mean    :",
    round(final_df["soil_wetness_gwet_top"].mean(), 4)
)


print("\nElevation:")
print(
    "Minimum :",
    round(final_df["elevation_m"].min(), 4)
)
print(
    "Maximum :",
    round(final_df["elevation_m"].max(), 4)
)
print(
    "Mean    :",
    round(final_df["elevation_m"].mean(), 4)
)


print("\nSlope:")
print(
    "Minimum :",
    round(final_df["slope_degrees"].min(), 4)
)
print(
    "Maximum :",
    round(final_df["slope_degrees"].max(), 4)
)
print(
    "Mean    :",
    round(final_df["slope_degrees"].mean(), 4)
)


# ============================================================
# CLASS-WISE FEATURE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("CLASS-WISE FEATURE SUMMARY")
print("=" * 70)

summary = (
    final_df
    .groupby("historical_landslide")[
        [
            "rainfall_mm_day",
            "soil_wetness_gwet_top",
            "elevation_m",
            "slope_degrees"
        ]
    ]
    .mean()
)

print(summary)


# ============================================================
# SAVE
# ============================================================

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL ML DATASET V2 CREATED")
print("=" * 70)

print("Total records :", len(final_df))
print(
    "Landslide     :",
    int((final_df["historical_landslide"] == 1).sum())
)
print(
    "Background    :",
    int((final_df["historical_landslide"] == 0).sum())
)

print("\nColumns:")

for col in final_df.columns:
    print(" -", col)

print("\nOutput file:")
print(
    OUTPUT_FILE.relative_to(BASE_DIR)
)

print("=" * 70)