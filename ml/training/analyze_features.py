import pandas as pd
from pathlib import Path


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_ml_dataset_v2.csv"
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "rainfall_mm_day",
    "soil_wetness_gwet_top",
    "slope_degrees",
    "elevation_m"
]

TARGET = "historical_landslide"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 75)
print("LANDSLIDE FEATURE RELATIONSHIP ANALYSIS")
print("=" * 75)

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

print("Total records:", len(df))


# ============================================================
# CLASS LABELS
# ============================================================

print("\nClass distribution:")

print(
    df[TARGET].value_counts()
    .sort_index()
)


# ============================================================
# CLASS-WISE STATISTICS
# ============================================================

print("\n")
print("=" * 75)
print("CLASS-WISE FEATURE STATISTICS")
print("=" * 75)

for feature in FEATURES:

    print("\n" + "-" * 75)

    print("Feature:", feature)

    print("-" * 75)

    class_0 = df[
        df[TARGET] == 0
    ][feature]

    class_1 = df[
        df[TARGET] == 1
    ][feature]

    print(
        f"Background   Mean   : {class_0.mean():.4f}"
    )

    print(
        f"Background   Median : {class_0.median():.4f}"
    )

    print(
        f"Background   Min    : {class_0.min():.4f}"
    )

    print(
        f"Background   Max    : {class_0.max():.4f}"
    )

    print()

    print(
        f"Landslide    Mean   : {class_1.mean():.4f}"
    )

    print(
        f"Landslide    Median : {class_1.median():.4f}"
    )

    print(
        f"Landslide    Min    : {class_1.min():.4f}"
    )

    print(
        f"Landslide    Max    : {class_1.max():.4f}"
    )


# ============================================================
# DIFFERENCE BETWEEN CLASSES
# ============================================================

print("\n")
print("=" * 75)
print("CLASS DIFFERENCE")
print("=" * 75)

comparison = []

for feature in FEATURES:

    background_mean = df[
        df[TARGET] == 0
    ][feature].mean()

    landslide_mean = df[
        df[TARGET] == 1
    ][feature].mean()

    difference = (
        landslide_mean
        - background_mean
    )

    comparison.append(
        {
            "feature": feature,
            "background_mean": background_mean,
            "landslide_mean": landslide_mean,
            "difference": difference
        }
    )


comparison_df = pd.DataFrame(
    comparison
)


for _, row in comparison_df.iterrows():

    print(
        f"\n{row['feature']}"
    )

    print(
        f"Background mean : "
        f"{row['background_mean']:.4f}"
    )

    print(
        f"Landslide mean  : "
        f"{row['landslide_mean']:.4f}"
    )

    print(
        f"Difference      : "
        f"{row['difference']:.4f}"
    )


# ============================================================
# RAINFALL THRESHOLDS
# ============================================================

print("\n")
print("=" * 75)
print("RAINFALL THRESHOLD ANALYSIS")
print("=" * 75)

thresholds = [
    25,
    50,
    75,
    100,
    150,
    200
]

for threshold in thresholds:

    background_count = (
        (
            df[df[TARGET] == 0]["rainfall_mm_day"]
            >= threshold
        ).sum()
    )

    landslide_count = (
        (
            df[df[TARGET] == 1]["rainfall_mm_day"]
            >= threshold
        ).sum()
    )

    background_total = (
        df[TARGET] == 0
    ).sum()

    landslide_total = (
        df[TARGET] == 1
    ).sum()

    background_percent = (
        background_count
        / background_total
        * 100
    )

    landslide_percent = (
        landslide_count
        / landslide_total
        * 100
    )

    print(
        f"\nRainfall >= {threshold} mm/day"
    )

    print(
        f"Background : "
        f"{background_count}/{background_total} "
        f"({background_percent:.2f}%)"
    )

    print(
        f"Landslide  : "
        f"{landslide_count}/{landslide_total} "
        f"({landslide_percent:.2f}%)"
    )


# ============================================================
# SLOPE THRESHOLDS
# ============================================================

print("\n")
print("=" * 75)
print("SLOPE THRESHOLD ANALYSIS")
print("=" * 75)

slope_thresholds = [
    10,
    20,
    30,
    40,
    50
]

for threshold in slope_thresholds:

    background_count = (
        (
            df[df[TARGET] == 0]["slope_degrees"]
            >= threshold
        ).sum()
    )

    landslide_count = (
        (
            df[df[TARGET] == 1]["slope_degrees"]
            >= threshold
        ).sum()
    )

    background_total = (
        df[TARGET] == 0
    ).sum()

    landslide_total = (
        df[TARGET] == 1
    ).sum()

    background_percent = (
        background_count
        / background_total
        * 100
    )

    landslide_percent = (
        landslide_count
        / landslide_total
        * 100
    )

    print(
        f"\nSlope >= {threshold} degrees"
    )

    print(
        f"Background : "
        f"{background_count}/{background_total} "
        f"({background_percent:.2f}%)"
    )

    print(
        f"Landslide  : "
        f"{landslide_count}/{landslide_total} "
        f"({landslide_percent:.2f}%)"
    )


# ============================================================
# SOIL WETNESS THRESHOLDS
# ============================================================

print("\n")
print("=" * 75)
print("SOIL WETNESS THRESHOLD ANALYSIS")
print("=" * 75)

soil_thresholds = [
    0.60,
    0.70,
    0.80,
    0.90,
    0.95
]

for threshold in soil_thresholds:

    background_count = (
        (
            df[df[TARGET] == 0]
            ["soil_wetness_gwet_top"]
            >= threshold
        ).sum()
    )

    landslide_count = (
        (
            df[df[TARGET] == 1]
            ["soil_wetness_gwet_top"]
            >= threshold
        ).sum()
    )

    background_total = (
        df[TARGET] == 0
    ).sum()

    landslide_total = (
        df[TARGET] == 1
    ).sum()

    background_percent = (
        background_count
        / background_total
        * 100
    )

    landslide_percent = (
        landslide_count
        / landslide_total
        * 100
    )

    print(
        f"\nSoil wetness >= {threshold}"
    )

    print(
        f"Background : "
        f"{background_count}/{background_total} "
        f"({background_percent:.2f}%)"
    )

    print(
        f"Landslide  : "
        f"{landslide_count}/{landslide_total} "
        f"({landslide_percent:.2f}%)"
    )


# ============================================================
# CORRELATION MATRIX
# ============================================================

print("\n")
print("=" * 75)
print("FEATURE CORRELATION MATRIX")
print("=" * 75)

correlation = df[
    FEATURES
].corr()

print(
    correlation.round(3)
)


# ============================================================
# SAVE SUMMARY
# ============================================================

output_file = (
    BASE_DIR
    / "data"
    / "processed"
    / "feature_analysis_summary.csv"
)

comparison_df.to_csv(
    output_file,
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 75)
print("FEATURE ANALYSIS COMPLETE")
print("=" * 75)

print(
    "\nSummary saved to:"
)

print(
    output_file.relative_to(BASE_DIR)
)

print("=" * 75)