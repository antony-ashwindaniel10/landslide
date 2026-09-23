import pandas as pd
from pathlib import Path

# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAINFALL_FILE = BASE_DIR / "data" / "processed" / "background_rainfall_features.csv"
SOIL_FILE = BASE_DIR / "data" / "processed" / "background_soil_moisture_power.csv"
DEM_FILE = BASE_DIR / "data" / "processed" / "background_dem_features.csv"

OUTPUT_FILE = BASE_DIR / "data" / "processed" / "background_ml_features_v2.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("BUILDING BACKGROUND ML FEATURES V2")
print("=" * 70)

print("\nLoading rainfall data...")
rainfall = pd.read_csv(RAINFALL_FILE)

print("Rainfall records :", len(rainfall))


print("\nLoading soil wetness data...")
soil = pd.read_csv(SOIL_FILE)

print("Soil records     :", len(soil))


print("\nLoading DEM data...")
dem = pd.read_csv(DEM_FILE)

print("DEM records      :", len(dem))


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

rainfall.columns = rainfall.columns.str.strip()
soil.columns = soil.columns.str.strip()
dem.columns = dem.columns.str.strip()


# ============================================================
# CONVERT DATES
# ============================================================

if "event_date" in rainfall.columns:
    rainfall["event_date"] = pd.to_datetime(
        rainfall["event_date"],
        errors="coerce"
    )

if "event_date" in soil.columns:
    soil["event_date"] = pd.to_datetime(
        soil["event_date"],
        errors="coerce"
    )


# ============================================================
# MERGE RAINFALL + SOIL
# ============================================================

print("\nMerging rainfall + soil wetness...")

merged = rainfall.merge(
    soil,
    on=["latitude", "longitude", "event_date"],
    how="inner"
)

print("After rainfall + soil merge:", len(merged))


# ============================================================
# MERGE DEM
# ============================================================

print("\nMerging DEM features...")

merged = merged.merge(
    dem[
        [
            "latitude",
            "longitude",
            "elevation_m",
            "slope_degrees"
        ]
    ],
    on=["latitude", "longitude"],
    how="left"
)

print("After DEM merge:", len(merged))


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before_duplicates = len(merged)

merged = merged.drop_duplicates(
    subset=["latitude", "longitude", "event_date"]
).copy()

duplicates_removed = before_duplicates - len(merged)

print("Duplicate records removed:", duplicates_removed)


# ============================================================
# SELECT FINAL COLUMNS
# ============================================================

final_columns = [
    "latitude",
    "longitude",
    "event_date",
    "rainfall_mm_day",
    "elevation_m",
    "slope_degrees",
    "soil_wetness_gwet_top",
    "soil_moisture_source"
]

missing_columns = [
    col for col in final_columns
    if col not in merged.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")
    for col in missing_columns:
        print(" -", col)

    raise SystemExit(1)


merged = merged[final_columns].copy()


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "latitude",
    "longitude",
    "rainfall_mm_day",
    "elevation_m",
    "slope_degrees",
    "soil_wetness_gwet_top"
]

for col in numeric_columns:
    merged[col] = pd.to_numeric(
        merged[col],
        errors="coerce"
    )


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print("\nMissing values:")

print(
    merged[
        final_columns
    ].isna().sum()
)


# ============================================================
# SAVE
# ============================================================

merged.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# STATISTICS
# ============================================================

print("\n" + "=" * 70)
print("BACKGROUND ML FEATURES V2 COMPLETE")
print("=" * 70)

print("Final records:", len(merged))

print("\nRainfall:")
print("Minimum :", round(merged["rainfall_mm_day"].min(), 4))
print("Maximum :", round(merged["rainfall_mm_day"].max(), 4))
print("Mean    :", round(merged["rainfall_mm_day"].mean(), 4))

print("\nSoil wetness:")
print("Minimum :", round(merged["soil_wetness_gwet_top"].min(), 4))
print("Maximum :", round(merged["soil_wetness_gwet_top"].max(), 4))
print("Mean    :", round(merged["soil_wetness_gwet_top"].mean(), 4))

print("\nElevation:")
print("Minimum :", round(merged["elevation_m"].min(), 4))
print("Maximum :", round(merged["elevation_m"].max(), 4))

print("\nSlope:")
print("Minimum :", round(merged["slope_degrees"].min(), 4))
print("Maximum :", round(merged["slope_degrees"].max(), 4))

print("\nSoil moisture sources:")
print(
    merged["soil_moisture_source"]
    .value_counts(dropna=False)
)

print("\nOutput file:")
print(
    OUTPUT_FILE.relative_to(BASE_DIR)
)

print("=" * 70)