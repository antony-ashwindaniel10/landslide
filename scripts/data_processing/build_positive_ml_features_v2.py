import pandas as pd

# ============================================================
# FILES
# ============================================================

RAIN_FILE = "data/processed/event_rainfall_features.csv"
SOIL_FILE = "data/processed/event_soil_moisture_power.csv"
DEM_FILE = "data/processed/dem_features.csv"

OUTPUT_FILE = "data/processed/positive_ml_features_v2.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("BUILDING POSITIVE ML FEATURES WITH SOIL WETNESS")
print("=" * 70)

rain = pd.read_csv(RAIN_FILE)
soil = pd.read_csv(SOIL_FILE)
dem = pd.read_csv(DEM_FILE)

print(f"Rainfall records : {len(rain)}")
print(f"Soil records     : {len(soil)}")
print(f"DEM records      : {len(dem)}")


# ============================================================
# PREPARE DATE
# ============================================================

rain["event_date"] = pd.to_datetime(rain["event_date"]).dt.strftime("%Y-%m-%d")
soil["event_date"] = pd.to_datetime(soil["event_date"]).dt.strftime("%Y-%m-%d")


# ============================================================
# MERGE RAINFALL + SOIL
# ============================================================

df = rain.merge(
    soil[
        [
            "latitude",
            "longitude",
            "event_date",
            "soil_wetness_gwet_top",
            "soil_moisture_source",
        ]
    ],
    on=["latitude", "longitude", "event_date"],
    how="left",
)

print(f"\nAfter rainfall + soil merge: {len(df)}")


# ============================================================
# MERGE DEM
# ============================================================

df = df.merge(
    dem[
        [
            "latitude",
            "longitude",
            "elevation_m",
            "slope_degrees",
        ]
    ],
    on=["latitude", "longitude"],
    how="left",
)

print(f"After DEM merge: {len(df)}")


# ============================================================
# ADD TARGET
# ============================================================

df["historical_landslide"] = 1


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates(
    subset=["latitude", "longitude", "event_date"]
).reset_index(drop=True)

removed = before - len(df)

print(f"Duplicate records removed: {removed}")


# ============================================================
# SELECT FINAL COLUMNS
# ============================================================

df = df[
    [
        "latitude",
        "longitude",
        "event_date",
        "rainfall_mm_day",
        "soil_wetness_gwet_top",
        "soil_moisture_source",
        "elevation_m",
        "slope_degrees",
        "historical_landslide",
    ]
]


# ============================================================
# VALIDATION
# ============================================================

print("\nMissing values:")
print(df.isnull().sum())

print("\nFinal positive records:")
print(len(df))

print("\nSoil wetness statistics:")
print(f"Minimum : {df['soil_wetness_gwet_top'].min():.4f}")
print(f"Maximum : {df['soil_wetness_gwet_top'].max():.4f}")
print(f"Mean    : {df['soil_wetness_gwet_top'].mean():.4f}")

print("\nRainfall statistics:")
print(f"Minimum : {df['rainfall_mm_day'].min():.4f}")
print(f"Maximum : {df['rainfall_mm_day'].max():.4f}")
print(f"Mean    : {df['rainfall_mm_day'].mean():.4f}")

print("\nElevation statistics:")
print(f"Minimum : {df['elevation_m'].min():.2f}")
print(f"Maximum : {df['elevation_m'].max():.2f}")

print("\nSlope statistics:")
print(f"Minimum : {df['slope_degrees'].min():.2f}")
print(f"Maximum : {df['slope_degrees'].max():.2f}")


# ============================================================
# SAVE
# ============================================================

df.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 70)
print("POSITIVE ML FEATURE BUILD COMPLETE")
print("=" * 70)

print(f"Output file:")
print(OUTPUT_FILE)