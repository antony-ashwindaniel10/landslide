import pandas as pd
import numpy as np

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.neighbors import BallTree


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
# SETTINGS
# ============================================================

TEST_SIZE = 0.20
RANDOM_STATE = 42

EARTH_RADIUS_KM = 6371.0088


# ============================================================
# START
# ============================================================

print("=" * 75)
print("SPATIAL LEAKAGE CHECK")
print("=" * 75)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

print(
    "Total records:",
    len(df)
)


# ============================================================
# CREATE RANDOM SPLIT
# ============================================================

train_df, test_df = train_test_split(
    df,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=df["historical_landslide"]
)


print("\nRandom 80/20 split:")

print(
    "Training records:",
    len(train_df)
)

print(
    "Testing records :",
    len(test_df)
)


# ============================================================
# PREPARE COORDINATES
# ============================================================

train_coords = np.radians(
    train_df[
        ["latitude", "longitude"]
    ].values
)

test_coords = np.radians(
    test_df[
        ["latitude", "longitude"]
    ].values
)


# ============================================================
# BUILD TREE
# ============================================================

print(
    "\nBuilding spatial index from training points..."
)

tree = BallTree(
    train_coords,
    metric="haversine"
)


# ============================================================
# FIND NEAREST TRAIN POINT
# ============================================================

distances, indices = tree.query(
    test_coords,
    k=1
)


nearest_distance_km = (
    distances[:, 0]
    * EARTH_RADIUS_KM
)


# ============================================================
# STATISTICS
# ============================================================

print("\n")
print("=" * 75)
print("NEAREST TRAINING-POINT DISTANCE")
print("=" * 75)


print(
    "\nMinimum distance :",
    round(
        nearest_distance_km.min(),
        3
    ),
    "km"
)

print(
    "Maximum distance :",
    round(
        nearest_distance_km.max(),
        3
    ),
    "km"
)

print(
    "Mean distance    :",
    round(
        nearest_distance_km.mean(),
        3
    ),
    "km"
)

print(
    "Median distance  :",
    round(
        np.median(nearest_distance_km),
        3
    ),
    "km"
)


# ============================================================
# DISTANCE DISTRIBUTION
# ============================================================

print("\n")
print("=" * 75)
print("TEST POINTS CLOSE TO TRAINING POINTS")
print("=" * 75)


thresholds = [
    0.5,
    1,
    2,
    5,
    10,
    25,
    50
]


for threshold in thresholds:

    count = (
        nearest_distance_km
        <= threshold
    ).sum()

    percentage = (
        count
        / len(test_df)
        * 100
    )

    print(
        f"Within {threshold:>5} km : "
        f"{count:>4} "
        f"({percentage:>6.2f}%)"
    )


# ============================================================
# VERY CLOSE TEST POINTS
# ============================================================

very_close = (
    nearest_distance_km <= 1
).sum()


close = (
    nearest_distance_km <= 5
).sum()


print("\n")
print("=" * 75)
print("INTERPRETATION")
print("=" * 75)


if very_close > 0:

    print(
        f"\n{very_close} test records are within "
        "1 km of a training record."
    )

else:

    print(
        "\nNo test records are within 1 km "
        "of a training record."
    )


print(
    f"{close} test records are within "
    "5 km of a training record."
)


print(
    "\nThis check does not change the dataset."
)

print(
    "It only measures how geographically close "
    "the random train/test split is."
)


print("\n")
print("=" * 75)
print("SPATIAL LEAKAGE CHECK COMPLETE")
print("=" * 75)