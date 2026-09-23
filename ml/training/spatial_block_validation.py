# ============================================================
# SPATIAL BLOCK VALIDATION - LANDSLIDE MODEL V2
# ============================================================

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score, roc_auc_score


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
print("SPATIAL BLOCK VALIDATION")
print("=" * 70)

df = pd.read_csv(DATA_FILE)

print("\nDataset records:", len(df))


# ============================================================
# CHECK REQUIRED COLUMNS
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
# REMOVE INVALID RECORDS
# ============================================================

df = df.dropna(subset=required_columns).copy()

print("Records after cleaning:", len(df))


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


# ============================================================
# BLOCK INFORMATION
# ============================================================

number_of_blocks = df["spatial_block"].nunique()

print("\nSpatial block size:", BLOCK_SIZE_DEGREES, "degrees")
print("Number of spatial blocks:", number_of_blocks)


# ============================================================
# BLOCK CLASS DISTRIBUTION
# ============================================================

block_summary = (
    df.groupby("spatial_block")[TARGET]
    .agg(["count", "sum"])
)

print("\nBlocks containing both classes:")

both_class_blocks = (
    (block_summary["sum"] > 0)
    &
    (block_summary["sum"] < block_summary["count"])
).sum()

print(both_class_blocks)


# ============================================================
# FEATURES / TARGET / GROUPS
# ============================================================

X = df[FEATURES]

y = df[TARGET].astype(int)

groups = df["spatial_block"]


# ============================================================
# SPATIAL CROSS VALIDATION
# ============================================================

cv = StratifiedGroupKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)


# ============================================================
# STORE RESULTS
# ============================================================

accuracy_scores = []

roc_auc_scores = []


# ============================================================
# FOLD LOOP
# ============================================================

for fold, (train_idx, test_idx) in enumerate(
    cv.split(X, y, groups),
    start=1
):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    train_groups = groups.iloc[train_idx]
    test_groups = groups.iloc[test_idx]


    print("\n" + "=" * 70)
    print("FOLD", fold)
    print("=" * 70)

    print("Training records:", len(train_idx))
    print("Testing records :", len(test_idx))

    print(
        "Training classes:",
        dict(y_train.value_counts().sort_index())
    )

    print(
        "Testing classes :",
        dict(y_test.value_counts().sort_index())
    )

    print(
        "Training blocks:",
        train_groups.nunique()
    )

    print(
        "Testing blocks :",
        test_groups.nunique()
    )


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

    model.fit(X_train, y_train)


    # ========================================================
    # PREDICTION
    # ========================================================

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(X_test)[:, 1]


    # ========================================================
    # METRICS
    # ========================================================

    accuracy = accuracy_score(
        y_test,
        predictions
    )


    # ROC-AUC requires both classes
    if len(np.unique(y_test)) == 2:

        roc_auc = roc_auc_score(
            y_test,
            probabilities
        )

    else:

        roc_auc = np.nan


    accuracy_scores.append(accuracy)

    roc_auc_scores.append(roc_auc)


    print("\nFold accuracy:", round(accuracy, 4))

    if not np.isnan(roc_auc):

        print(
            "Fold ROC-AUC:",
            round(roc_auc, 4)
        )

    else:

        print(
            "Fold ROC-AUC: Not available "
            "(only one class in test set)"
        )


# ============================================================
# FINAL RESULTS
# ============================================================

print("\n\n")
print("=" * 70)
print("SPATIAL BLOCK VALIDATION RESULTS")
print("=" * 70)


for i in range(N_SPLITS):

    print(
        f"Fold {i + 1}: "
        f"Accuracy = {accuracy_scores[i]:.4f}, "
        f"ROC-AUC = "
        f"{roc_auc_scores[i]:.4f}"
        if not np.isnan(roc_auc_scores[i])
        else
        f"Fold {i + 1}: "
        f"Accuracy = {accuracy_scores[i]:.4f}, "
        f"ROC-AUC = N/A"
    )


# ============================================================
# MEAN RESULTS
# ============================================================

mean_accuracy = np.mean(
    accuracy_scores
)

valid_auc = [
    score
    for score in roc_auc_scores
    if not np.isnan(score)
]

if valid_auc:

    mean_roc_auc = np.mean(valid_auc)

else:

    mean_roc_auc = np.nan


print("\n" + "=" * 70)

print(
    "Mean Accuracy:",
    round(mean_accuracy, 4)
)

if not np.isnan(mean_roc_auc):

    print(
        "Mean ROC-AUC:",
        round(mean_roc_auc, 4)
    )

else:

    print(
        "Mean ROC-AUC: N/A"
    )


# ============================================================
# INTERPRETATION
# ============================================================

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

print("""
This validation uses geographic blocks instead of a random
train/test split.

Therefore, records from the same spatial block are kept
together and are not shared between training and testing.

This gives a more realistic estimate of how the model may
perform in geographically unseen areas.

The random-split accuracy should NOT be used as the main
generalization result.

Spatial-block validation is a stronger test for this project.
""")


print("\n" + "=" * 70)
print("SPATIAL BLOCK VALIDATION COMPLETE")
print("=" * 70)