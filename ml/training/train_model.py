import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)


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

MODEL_DIR = BASE_DIR / "ml" / "models"

MODEL_FILE = MODEL_DIR / "landslide_risk_model_v2.pkl"


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "rainfall_mm_day",
    "soil_wetness_gwet_top",
    "slope_degrees",
    "elevation_m",
    "latitude",
    "longitude"
]

TARGET = "historical_landslide"


# ============================================================
# START
# ============================================================

print("=" * 75)
print("LANDSLIDE RISK MODEL V2 - RANDOM FOREST")
print("=" * 75)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

print("Dataset records:", len(df))


# ============================================================
# CHECK COLUMNS
# ============================================================

print("\nChecking required columns...")

required_columns = FEATURES + [TARGET]

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

before_cleaning = len(df)

df = df.dropna(
    subset=required_columns
).copy()

removed = before_cleaning - len(df)

print("\nRecords removed because of missing values:", removed)
print("Records available for training:", len(df))


# ============================================================
# PREPARE X AND Y
# ============================================================

X = df[FEATURES]

y = df[TARGET]


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("\nClass distribution:")

print(
    y.value_counts()
    .sort_index()
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print("\nCreating 80/20 stratified train-test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\nTraining records:", len(X_train))
print("Testing records :", len(X_test))


print("\nTraining class distribution:")

print(
    y_train.value_counts()
    .sort_index()
)


print("\nTesting class distribution:")

print(
    y_test.value_counts()
    .sort_index()
)


# ============================================================
# RANDOM FOREST MODEL
# ============================================================

print("\nTraining Random Forest model...")

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


print("Model training completed.")


# ============================================================
# PREDICTION
# ============================================================

print("\nGenerating test predictions...")

y_pred = model.predict(X_test)

y_probability = model.predict_proba(
    X_test
)[:, 1]


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n" + "=" * 75)
print("MODEL EVALUATION")
print("=" * 75)

print(
    "\nAccuracy:",
    round(accuracy, 4)
)


# ============================================================
# ROC-AUC
# ============================================================

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

print(
    "ROC-AUC:",
    round(roc_auc, 4)
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        digits=4
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("Confusion Matrix:")

cm = confusion_matrix(
    y_test,
    y_pred
)

print(cm)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 75)
print("FEATURE IMPORTANCE")
print("=" * 75)

importance = pd.DataFrame(
    {
        "feature": FEATURES,
        "importance": model.feature_importances_
    }
)

importance = importance.sort_values(
    by="importance",
    ascending=False
)

for _, row in importance.iterrows():

    print(
        f"{row['feature']:<30} "
        f"{row['importance']:.4f}"
    )


# ============================================================
# SAVE MODEL
# ============================================================

print("\n" + "=" * 75)
print("SAVING MODEL")
print("=" * 75)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_FILE
)

print("\nModel saved successfully:")

print(
    MODEL_FILE.relative_to(BASE_DIR)
)


# ============================================================
# MODEL INFORMATION
# ============================================================

print("\nModel configuration:")

print("Algorithm       : Random Forest")
print("Trees           :", model.n_estimators)
print("Max depth       :", model.max_depth)
print("Min samples leaf:", model.min_samples_leaf)
print("Class weight    :", model.class_weight)

print("\nFeatures used:")

for feature in FEATURES:
    print(" -", feature)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 75)
print("MODEL TRAINING COMPLETE")
print("=" * 75)

print(
    "\nTest Accuracy :",
    round(accuracy, 4)
)

print(
    "Test ROC-AUC  :",
    round(roc_auc, 4)
)

print("\nNext step will be geographic validation of this new model.")

print("=" * 75)