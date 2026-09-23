import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.neighbors import BallTree


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
    / "background_distance_analysis.csv"
)


# ============================================================
# EARTH RADIUS
# ============================================================

EARTH_RADIUS_KM = 6371.0088


# ============================================================
# START
# ============================================================

print("=" * 75)
print("BACKGROUND POINT SPATIAL DISTANCE ANALYSIS")
print("=" * 75)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading positive landslide records...")

positive = pd.read_csv(
    POSITIVE_FILE
)

print(
    "Positive records:",
    len(positive)
)


print("\nLoading background records...")

background = pd.read_csv(
    BACKGROUND_FILE
)

print(
    "Background records:",
    len(background)
)


# ============================================================
# CHECK COORDINATES
# ============================================================

required = [
    "latitude",
    "longitude"
]

for column in required:

    if column not in positive.columns:

        raise SystemExit(
            f"Missing {column} in positive dataset"
        )

    if column not in background.columns:

        raise SystemExit(
            f"Missing {column} in background dataset"
        )


# ============================================================
# PREPARE COORDINATES
# ============================================================

positive_coords = np.radians(
    positive[
        ["latitude", "longitude"]
    ].values
)

background_coords = np.radians(
    background[
        ["latitude", "longitude"]
    ].values
)


# ============================================================
# BUILD SPATIAL TREE
# ============================================================

print("\nBuilding spatial index...")

tree = BallTree(
    positive_coords,
    metric="haversine"
)


# ============================================================
# FIND NEAREST LANDSLIDE
# ============================================================

print(
    "\nFinding nearest historical landslide "
    "for every background point..."
)

distances, indices = tree.query(
    background_coords,
    k=1
)


# Convert radians to kilometres

nearest_distance_km = (
    distances[:, 0]
    * EARTH_RADIUS_KM
)


nearest_index = (
    indices[:, 0]
)


# ============================================================
# ADD RESULTS
# ============================================================

background_analysis = background.copy()

background_analysis[
    "nearest_landslide_distance_km"
] = nearest_distance_km


background_analysis[
    "nearest_landslide_latitude"
] = positive.iloc[
    nearest_index
]["latitude"].values


background_analysis[
    "nearest_landslide_longitude"
] = positive.iloc[
    nearest_index
]["longitude"].values


# ============================================================
# DISTANCE STATISTICS
# ============================================================

print("\n")
print("=" * 75)
print("DISTANCE STATISTICS")
print("=" * 75)


distance = background_analysis[
    "nearest_landslide_distance_km"
]


print(
    "\nMinimum distance :",
    round(distance.min(), 2),
    "km"
)

print(
    "Maximum distance :",
    round(distance.max(), 2),
    "km"
)

print(
    "Mean distance    :",
    round(distance.mean(), 2),
    "km"
)

print(
    "Median distance  :",
    round(distance.median(), 2),
    "km"
)


# ============================================================
# DISTANCE BINS
# ============================================================

print("\n")
print("=" * 75)
print("BACKGROUND POINT DISTANCE DISTRIBUTION")
print("=" * 75)


bins = [
    0,
    1,
    5,
    10,
    25,
    50,
    100,
    250,
    500,
    np.inf
]


labels = [
    "<1 km",
    "1-5 km",
    "5-10 km",
    "10-25 km",
    "25-50 km",
    "50-100 km",
    "100-250 km",
    "250-500 km",
    ">500 km"
]


distance_category = pd.cut(
    distance,
    bins=bins,
    labels=labels,
    right=False
)


distribution = (
    distance_category
    .value_counts(
        sort=False
    )
)


total = len(distance)


for category, count in distribution.items():

    percentage = (
        count
        / total
        * 100
    )

    print(
        f"{str(category):<12}"
        f"{count:>7} "
        f"({percentage:>6.2f}%)"
    )


# ============================================================
# THRESHOLD COUNTS
# ============================================================

print("\n")
print("=" * 75)
print("DISTANCE THRESHOLD ANALYSIS")
print("=" * 75)


thresholds = [
    1,
    5,
    10,
    25,
    50,
    100,
    250,
    500
]


for threshold in thresholds:

    count = (
        distance <= threshold
    ).sum()

    percentage = (
        count
        / total
        * 100
    )

    print(
        f"Within {threshold:>3} km : "
        f"{count:>5} "
        f"({percentage:.2f}%)"
    )


# ============================================================
# SAVE
# ============================================================

background_analysis.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 75)
print("ANALYSIS COMPLETE")
print("=" * 75)

print(
    "\nOutput:"
)

print(
    OUTPUT_FILE.relative_to(BASE_DIR)
)

print("=" * 75)