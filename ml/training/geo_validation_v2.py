import pandas as pd
import geopandas as gpd

from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_ml_dataset_v2.csv"
)

BOUNDARY_FILE = (
    BASE_DIR
    / "data"
    / "boundaries"
    / "NER_states.geojson"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "geographic_validation_v2.csv"
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
# START
# ============================================================

print("=" * 75)
print("LANDSLIDE RISK MODEL V2 - GEOGRAPHIC VALIDATION")
print("=" * 75)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading ML dataset...")

df = pd.read_csv(DATA_FILE)

print("Total records:", len(df))


# ============================================================
# CHECK COLUMNS
# ============================================================

required_columns = [
    "latitude",
    "longitude",
    *FEATURES,
    TARGET
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("\nERROR: Missing columns:")

    for column in missing_columns:
        print(" -", column)

    raise SystemExit(1)

print("All required columns found.")


# ============================================================
# REMOVE MISSING VALUES
# ============================================================

before = len(df)

df = df.dropna(
    subset=required_columns
).copy()

removed = before - len(df)

print("\nMissing-value records removed:", removed)
print("Records available:", len(df))


# ============================================================
# LOAD NER BOUNDARY
# ============================================================

print("\nLoading NER state boundaries...")

states_gdf = gpd.read_file(
    BOUNDARY_FILE
)

print(
    "Boundary features:",
    len(states_gdf)
)

print(
    "Boundary state column: STNAME"
)


# ============================================================
# CREATE POINT GEOMETRY
# ============================================================

print("\nCreating geographic points...")

points_gdf = gpd.GeoDataFrame(
    df.copy(),
    geometry=gpd.points_from_xy(
        df["longitude"],
        df["latitude"]
    ),
    crs="EPSG:4326"
)


# ============================================================
# PREPARE BOUNDARY
# ============================================================

if states_gdf.crs is None:

    states_gdf = states_gdf.set_crs(
        "EPSG:4326"
    )

else:

    states_gdf = states_gdf.to_crs(
        "EPSG:4326"
    )


# ============================================================
# SPATIAL JOIN
# ============================================================

print("\nAssigning each record to an NER state...")

joined = gpd.sjoin(
    points_gdf,
    states_gdf[
        ["STNAME", "geometry"]
    ],
    how="left",
    predicate="within"
)


# ============================================================
# RENAME STATE
# ============================================================

joined = joined.rename(
    columns={
        "STNAME": "state"
    }
)


# ============================================================
# CHECK STATE ASSIGNMENT
# ============================================================

missing_states = joined["state"].isna().sum()

print(
    "\nRecords without state:",
    missing_states
)

if missing_states > 0:

    print(
        "\nWARNING: Some records were not inside "
        "an NER state boundary."
    )


# ============================================================
# REMOVE GEOMETRY
# ============================================================

df = pd.DataFrame(
    joined.drop(
        columns=[
            "geometry",
            "index_right"
        ],
        errors="ignore"
    )
)


# ============================================================
# STATE DISTRIBUTION
# ============================================================

print("\nState distribution:")

print(
    df["state"]
    .value_counts()
)


# ============================================================
# STATE LIST
# ============================================================

states = sorted(
    df["state"]
    .dropna()
    .unique()
)

print("\nStates found:")

for state in states:

    print(" -", state)


# ============================================================
# LEAVE-ONE-STATE-OUT VALIDATION
# ============================================================

results = []


print("\n")
print("=" * 75)
print("LEAVE-ONE-STATE-OUT VALIDATION")
print("=" * 75)

print(
    f"{'State':<22}"
    f"{'Test':>8}"
    f"{'Class 0':>10}"
    f"{'Class 1':>10}"
    f"{'Accuracy':>12}"
    f"{'ROC-AUC':>12}"
)

print("-" * 75)


for state in states:

    print(
        f"\nTesting {state}..."
    )


    # --------------------------------------------------------
    # TRAIN / TEST BY STATE
    # --------------------------------------------------------

    train_df = df[
        df["state"] != state
    ].copy()

    test_df = df[
        df["state"] == state
    ].copy()


    # --------------------------------------------------------
    # FEATURES AND TARGET
    # --------------------------------------------------------

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]


    # --------------------------------------------------------
    # CLASS COUNTS
    # --------------------------------------------------------

    class_counts = y_test.value_counts()

    class_0 = int(
        class_counts.get(0, 0)
    )

    class_1 = int(
        class_counts.get(1, 0)
    )


    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )


    # --------------------------------------------------------
    # PREDICTIONS
    # --------------------------------------------------------

    y_pred = model.predict(
        X_test
    )

    y_probability = model.predict_proba(
        X_test
    )[:, 1]


    # --------------------------------------------------------
    # ACCURACY
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred
    )


    # --------------------------------------------------------
    # ROC-AUC
    # --------------------------------------------------------

    if len(y_test.unique()) == 2:

        roc_auc = roc_auc_score(
            y_test,
            y_probability
        )

    else:

        roc_auc = float("nan")


    # --------------------------------------------------------
    # STORE RESULTS
    # --------------------------------------------------------

    results.append(
        {
            "state": state,
            "test_records": len(test_df),
            "class_0": class_0,
            "class_1": class_1,
            "accuracy": accuracy,
            "roc_auc": roc_auc
        }
    )


    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print(
        f"{state:<22}"
        f"{len(test_df):>8}"
        f"{class_0:>10}"
        f"{class_1:>10}"
        f"{accuracy:>12.4f}"
        f"{roc_auc:>12.4f}"
    )


# ============================================================
# RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(
    results
)


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 75)
print("OVERALL GEOGRAPHIC VALIDATION SUMMARY")
print("=" * 75)


mean_accuracy = results_df[
    "accuracy"
].mean()

mean_roc_auc = results_df[
    "roc_auc"
].mean()


print(
    "\nMean Accuracy:",
    round(mean_accuracy, 4)
)

print(
    "Mean ROC-AUC:",
    round(mean_roc_auc, 4)
)


# ============================================================
# BEST STATE
# ============================================================

best_state = results_df.loc[
    results_df["roc_auc"].idxmax()
]

print("\nBest state ROC-AUC:")

print(
    f"{best_state['state']} -> "
    f"{best_state['roc_auc']:.4f}"
)


# ============================================================
# WORST STATE
# ============================================================

worst_state = results_df.loc[
    results_df["roc_auc"].idxmin()
]

print("\nLowest state ROC-AUC:")

print(
    f"{worst_state['state']} -> "
    f"{worst_state['roc_auc']:.4f}"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n")
print("=" * 75)
print("FEATURE IMPORTANCE")
print("=" * 75)


final_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=10,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

final_model.fit(
    df[FEATURES],
    df[TARGET]
)


importance_df = pd.DataFrame(
    {
        "feature": FEATURES,
        "importance": final_model.feature_importances_
    }
)

importance_df = importance_df.sort_values(
    by="importance",
    ascending=False
)


for _, row in importance_df.iterrows():

    print(
        f"{row['feature']:<30}"
        f"{row['importance']:.4f}"
    )


# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n")
print("=" * 75)
print("VALIDATION COMPLETE")
print("=" * 75)

print("\nResults saved to:")

print(
    OUTPUT_FILE.relative_to(BASE_DIR)
)

print("\nFeatures used:")

for feature in FEATURES:
    print(" -", feature)

print(
    "\nLatitude and longitude were intentionally excluded."
)

print(
    "State was derived from STNAME in the NER boundary."
)

print("=" * 75)