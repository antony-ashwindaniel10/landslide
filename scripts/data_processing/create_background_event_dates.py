import os
import pandas as pd
import numpy as np

# ============================================================
# FILE PATHS
# ============================================================

EVENT_RAINFALL_FILE = "data/processed/event_rainfall_features.csv"
BACKGROUND_FILE = "data/processed/background_points.csv"
OUTPUT_FILE = "data/processed/background_event_dates.csv"


# ============================================================
# CHECK INPUT FILES
# ============================================================

if not os.path.exists(EVENT_RAINFALL_FILE):
    print("ERROR: Event rainfall file not found.")
    print(f"Expected: {EVENT_RAINFALL_FILE}")
    raise SystemExit

if not os.path.exists(BACKGROUND_FILE):
    print("ERROR: Background points file not found.")
    print(f"Expected: {BACKGROUND_FILE}")
    raise SystemExit


# ============================================================
# LOAD DATA
# ============================================================

events = pd.read_csv(EVENT_RAINFALL_FILE)
background = pd.read_csv(BACKGROUND_FILE)

print("=" * 70)
print("BACKGROUND EVENT DATE CREATION")
print("=" * 70)
print()

print(f"Event rainfall records : {len(events):,}")
print(f"Background points      : {len(background):,}")
print()


# ============================================================
# GET DATE DISTRIBUTION FROM LANDSLIDE EVENTS
# ============================================================

date_counts = (
    events["event_date"]
    .dropna()
    .value_counts()
    .sort_index()
)

print(f"Unique event dates      : {len(date_counts)}")
print(f"Total dated events      : {date_counts.sum():,}")
print()


# ============================================================
# CHECK BACKGROUND CAPACITY
# ============================================================

required_points = len(events)

if len(background) < required_points:
    print("ERROR: Not enough background points.")
    print(f"Required : {required_points:,}")
    print(f"Available: {len(background):,}")
    raise SystemExit


# ============================================================
# SELECT BACKGROUND POINTS
# ============================================================

# Use a fixed seed so the result is reproducible.
np.random.seed(42)

background_sample = background.sample(
    n=required_points,
    random_state=42
).reset_index(drop=True)


# ============================================================
# CREATE DATE ASSIGNMENT
# ============================================================

assigned_dates = []

for event_date, count in date_counts.items():
    assigned_dates.extend([event_date] * count)


# Safety check
if len(assigned_dates) != required_points:
    print("ERROR: Date assignment count does not match event count.")
    print(f"Assigned dates: {len(assigned_dates):,}")
    print(f"Required      : {required_points:,}")
    raise SystemExit


# ============================================================
# SHUFFLE DATES
# ============================================================

assigned_dates = np.array(assigned_dates)

rng = np.random.default_rng(42)
rng.shuffle(assigned_dates)


# ============================================================
# BUILD BACKGROUND EVENT DATASET
# ============================================================

background_sample["event_date"] = assigned_dates

background_sample["historical_landslide"] = 0


# ============================================================
# REORDER COLUMNS
# ============================================================

background_sample = background_sample[
    [
        "latitude",
        "longitude",
        "event_date",
        "historical_landslide"
    ]
]


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

background_sample.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("BACKGROUND EVENT DATASET CREATED")
print("-" * 70)

print(f"Records created : {len(background_sample):,}")
print(f"Unique dates    : {background_sample['event_date'].nunique()}")
print()

print("Class distribution:")
print(background_sample["historical_landslide"].value_counts())
print()

print("Date distribution comparison:")

event_distribution = (
    events["event_date"]
    .value_counts()
    .sort_index()
)

background_distribution = (
    background_sample["event_date"]
    .value_counts()
    .sort_index()
)

comparison = pd.DataFrame({
    "landslide": event_distribution,
    "background": background_distribution
}).fillna(0)

comparison["difference"] = (
    comparison["landslide"] -
    comparison["background"]
)

print(comparison.head(10))
print()

print(
    "Maximum date-count difference:",
    comparison["difference"].abs().max()
)

print()

print("Output file:")
print(OUTPUT_FILE)

print()
print("=" * 70)
print("COMPLETED")
print("=" * 70)