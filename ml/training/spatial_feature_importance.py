# ============================================================
# SPATIAL BLOCK FEATURE IMPORTANCE
# LANDSLIDE RISK MODEL V2
# ============================================================

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold


# ============================================================
# FILE
# ============================================================

DATA_FILE = "data/processed/final_ml_dataset_v2.csv"


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
# SETTINGS
# ============================================================

BLOCK_SIZE_DEGREES = 0.5

N_SPLITS = 5

RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("SPATIAL BLOCK FEATURE IMPORTANCE")
print("=" * 70)

df = pd.read_csv(DATA_FILE)

print("\nDataset records:", len(df))


# ============================================================
# CHECK COLUMNS
# ============================================================

required_columns = FEATURES + [
    TARGET,
    "latitude",
    "longitude"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    print("\nERROR: Missing columns:")

    for col in missing_columns:
        print(" -", col)

    raise SystemExit


# ============================================================
# CLEAN DATA
# ============================================================

df = df.dropna(
    subset=required_columns
).copy()

print(
    "Records after cleaning:",
    len(df)
)


# ============================================================
# CREATE SPATIAL BLOCKS
# ============================================================

df["lat_block"] = np.floor(
    df["latitude"] / BLOCK_SIZE_DEGREES
).astype(int)

df["lon_block"] = np.floor(
    df["longitude"] / BLOCK_SIZE_DEGREES
).astype(int)

df["spatial_block"] = (
    df["lat_block"].astype(str)
    + "_"
    + df["lon_block"].astype(str)
)


print(
    "Spatial blocks:",
    df["spatial_block"].nunique()
)


# ============================================================
# PREPARE DATA
# ============================================================

X = df[FEATURES]

y = df[TARGET].astype(int)

groups = df["spatial_block"]


# ============================================================
# CROSS VALIDATION
# ============================================================

cv = StratifiedGroupKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)


# ============================================================
# STORE IMPORTANCE
# ============================================================

importance_values = {
    feature: []
    for feature in FEATURES
}


# ============================================================
# FOLD LOOP
# ============================================================

for fold, (train_idx, test_idx) in enumerate(
    cv.split(X, y, groups),
    start=1
):

    print("\n" + "=" * 70)

    print(
        "Training fold:",
        fold
    )

    print("=" * 70)


    X_train = X.iloc[train_idx]

    y_train = y.iloc[train_idx]


    # ========================================================
    # MODEL
    # ========================================================

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )


    # ========================================================
    # TRAIN
    # ========================================================

    model.fit(
        X_train,
        y_train
    )


    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    fold_importance = model.feature_importances_


    print("\nFeature importance for this fold:")

    for feature, importance in zip(
        FEATURES,
        fold_importance
    ):

        print(
            f"{feature:30s}: "
            f"{importance:.4f}"
        )

        importance_values[
            feature
        ].append(importance)


# ============================================================
# AVERAGE IMPORTANCE
# ============================================================

mean_importance = {}

for feature in FEATURES:

    mean_importance[feature] = np.mean(
        importance_values[feature]
    )


# ============================================================
# NORMALIZE
# ============================================================

total_importance = sum(
    mean_importance.values()
)

normalized_importance = {
    feature:
        (importance / total_importance) * 100
    for feature, importance
    in mean_importance.items()
}


# ============================================================
# SORT
# ============================================================

sorted_features = sorted(
    normalized_importance.items(),
    key=lambda x: x[1],
    reverse=True
)


# ============================================================
# FINAL RESULTS
# ============================================================

print("\n\n")

print("=" * 70)
print("AVERAGE SPATIAL FEATURE IMPORTANCE")
print("=" * 70)

for rank, (feature, percentage) in enumerate(
    sorted_features,
    start=1
):

    print(
        f"{rank}. "
        f"{feature:30s} "
        f"{percentage:.2f}%"
    )


# ============================================================
# RAW IMPORTANCE
# ============================================================

print("\n" + "=" * 70)
print("RAW AVERAGE IMPORTANCE")
print("=" * 70)

for feature in FEATURES:

    print(
        f"{feature:30s}: "
        f"{mean_importance[feature]:.4f}"
    )


# ============================================================
# INTERPRETATION
# ============================================================

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

print("""
These values show how much each environmental feature
contributes to the Random Forest model across the
spatial validation folds.

The values are model feature importance values, not
physical causality.

A higher value means the model relied more heavily on
that feature when making its predictions.

This helps explain the AI risk model to SIH judges.
""")


# ============================================================
# SAVE RESULTS
# ============================================================

results = pd.DataFrame(
    [
        {
            "feature": feature,
            "mean_importance": mean_importance[feature],
            "importance_percent": normalized_importance[feature]
        }
        for feature in FEATURES
    ]
)

results = results.sort_values(
    "importance_percent",
    ascending=False
)

OUTPUT_FILE = (
    "data/processed/"
    "spatial_feature_importance.csv"
)

results.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nResults saved to:")

print(OUTPUT_FILE)


print("\n" + "=" * 70)
print("SPATIAL FEATURE IMPORTANCE COMPLETE")
print("=" * 70)