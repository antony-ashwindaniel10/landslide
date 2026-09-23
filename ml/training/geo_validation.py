import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score


# ============================================================
# FILES
# ============================================================

MASTER_FILE = "data/processed/master_landslide_dataset.csv"
FINAL_FILE = "data/processed/final_ml_dataset.csv"
BACKGROUND_FILE = "data/processed/background_points_with_state.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("Loading datasets...")

master = pd.read_csv(MASTER_FILE)
final = pd.read_csv(FINAL_FILE)
background = pd.read_csv(BACKGROUND_FILE)

print("Datasets loaded successfully.")


# ============================================================
# ADD STATE TO POSITIVE RECORDS
# ============================================================

positive = final[
    final["historical_landslide"] == 1
].copy()

state_map = master[
    ["latitude", "longitude", "state"]
].drop_duplicates(
    subset=["latitude", "longitude"]
)

positive = positive.merge(
    state_map,
    on=["latitude", "longitude"],
    how="left"
)


# ============================================================
# ADD STATE TO BACKGROUND RECORDS
# ============================================================

background_final = final[
    final["historical_landslide"] == 0
][
    [
        "latitude",
        "longitude",
        "rainfall_mm_day",
        "elevation_m",
        "slope_degrees",
        "historical_landslide"
    ]
].copy()

background_final = background_final.merge(
    background[
        ["latitude", "longitude", "state"]
    ],
    on=["latitude", "longitude"],
    how="left"
)


# ============================================================
# COMBINE
# ============================================================

positive = positive[
    [
        "latitude",
        "longitude",
        "rainfall_mm_day",
        "elevation_m",
        "slope_degrees",
        "historical_landslide",
        "state"
    ]
]

df = pd.concat(
    [positive, background_final],
    ignore_index=True
)


# ============================================================
# FEATURES
# ============================================================

features = [
    "rainfall_mm_day",
    "slope_degrees",
    "elevation_m"
]


# ============================================================
# STATES
# ============================================================

states = sorted(
    df["state"].dropna().unique()
)


# ============================================================
# LEAVE-ONE-STATE-OUT VALIDATION
# ============================================================

print()
print("=" * 75)
print(" LEAVE-ONE-STATE-OUT VALIDATION")
print("=" * 75)
print()

print(
    f"{'State':<22}"
    f"{'Test':>7}"
    f"{'Class 0':>9}"
    f"{'Class 1':>9}"
    f"{'Accuracy':>11}"
    f"{'ROC-AUC':>10}"
)

print("-" * 75)


results = []


for state in states:

    print(f"Testing {state}...")

    train = df[
        df["state"] != state
    ]

    test = df[
        df["state"] == state
    ]

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    model.fit(
        train[features],
        train["historical_landslide"]
    )

    probabilities = model.predict_proba(
        test[features]
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    accuracy = accuracy_score(
        test["historical_landslide"],
        predictions
    )

    # ROC-AUC requires both classes
    if test["historical_landslide"].nunique() == 2:
        roc_auc = roc_auc_score(
            test["historical_landslide"],
            probabilities
        )
    else:
        roc_auc = float("nan")

    class_0 = (
        test["historical_landslide"] == 0
    ).sum()

    class_1 = (
        test["historical_landslide"] == 1
    ).sum()

    results.append(
        {
            "state": state,
            "test_records": len(test),
            "class_0": class_0,
            "class_1": class_1,
            "accuracy": accuracy,
            "roc_auc": roc_auc
        }
    )

    print(
        f"{state:<22}"
        f"{len(test):>7}"
        f"{class_0:>9}"
        f"{class_1:>9}"
        f"{accuracy:>11.4f}"
        f"{roc_auc:>10.4f}"
    )


# ============================================================
# SUMMARY
# ============================================================

results_df = pd.DataFrame(results)

print()
print("=" * 75)
print(" OVERALL VALIDATION SUMMARY")
print("=" * 75)

print()

print(
    "Mean Accuracy:",
    round(results_df["accuracy"].mean(), 4)
)

print(
    "Mean ROC-AUC:",
    round(results_df["roc_auc"].mean(), 4)
)

print()

print("Best state ROC-AUC:")

best = results_df.loc[
    results_df["roc_auc"].idxmax()
]

print(
    best["state"],
    "->",
    round(best["roc_auc"], 4)
)

print()

print("Lowest state ROC-AUC:")

worst = results_df.loc[
    results_df["roc_auc"].idxmin()
]

print(
    worst["state"],
    "->",
    round(worst["roc_auc"], 4)
)

print()
print("Validation completed successfully.")