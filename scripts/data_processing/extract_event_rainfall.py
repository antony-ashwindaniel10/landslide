import os
import re
import pandas as pd
import numpy as np
import xarray as xr


# ============================================================
# FILE PATHS
# ============================================================

MASTER_FILE = "data/processed/master_landslide_dataset.csv"
WEATHER_DIR = "data/weather"
OUTPUT_FILE = "data/processed/event_rainfall_features.csv"


# ============================================================
# CHECK INPUT FILES
# ============================================================

if not os.path.exists(MASTER_FILE):
    print("ERROR: Master dataset not found.")
    print(f"Expected: {MASTER_FILE}")
    raise SystemExit

if not os.path.exists(WEATHER_DIR):
    print("ERROR: Weather directory not found.")
    print(f"Expected: {WEATHER_DIR}")
    raise SystemExit


# ============================================================
# LOAD MASTER DATASET
# ============================================================

print("=" * 70)
print("IMERG EVENT RAINFALL EXTRACTION")
print("=" * 70)
print()

df = pd.read_csv(MASTER_FILE)

print(f"Master records: {len(df):,}")

required_columns = [
    "sl_no",
    "latitude",
    "longitude",
    "history"
]

for column in required_columns:
    if column not in df.columns:
        print(f"ERROR: Required column missing: {column}")
        raise SystemExit


# ============================================================
# EXTRACT EXACT EVENT DATE FROM HISTORY
# ============================================================

def extract_event_date(value):

    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    # --------------------------------------------------------
    # Format: 16 June 2025
    # Format: 16 June, 2025
    # --------------------------------------------------------

    match = re.search(
        r"\b(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})\b",
        text
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        date = pd.to_datetime(
            f"{day} {month} {year}",
            errors="coerce"
        )

        if not pd.isna(date):
            return date

    # --------------------------------------------------------
    # Format: 16/06/2025
    # Format: 16-06-2025
    # --------------------------------------------------------

    match = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
        text
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        date = pd.to_datetime(
            f"{day}/{month}/{year}",
            format="%d/%m/%Y",
            errors="coerce"
        )

        if not pd.isna(date):
            return date

    return pd.NaT


print("Extracting exact event dates...")

df["event_date"] = df["history"].apply(
    extract_event_date
)

print(
    "Records with exact event date:",
    df["event_date"].notna().sum()
)

print(
    "Records without exact event date:",
    df["event_date"].isna().sum()
)

print()


# ============================================================
# PREPARE OUTPUT
# ============================================================

rainfall_records = []

processed = 0
failed = 0


# ============================================================
# CREATE WEATHER FILE INDEX
# ============================================================

print("Indexing IMERG files...")

weather_files = [
    file
    for file in os.listdir(WEATHER_DIR)
    if file.endswith(".nc4")
]

print(
    f"NetCDF files found: {len(weather_files)}"
)

print()


def find_weather_file(date_string):

    compact_date = date_string.replace("-", "")

    candidates = [
        file
        for file in weather_files
        if compact_date in file
        and "3IMERG" in file
    ]

    if not candidates:
        return None

    # Prefer Final Run when both Final and Late exist.
    final_files = [
        file
        for file in candidates
        if "3B-DAY-L." not in file
    ]

    if final_files:
        return os.path.join(
            WEATHER_DIR,
            final_files[0]
        )

    return os.path.join(
        WEATHER_DIR,
        candidates[0]
    )


# ============================================================
# CACHE OPENED DATASETS
# ============================================================

dataset_cache = {}


def get_dataset(file_path):

    if file_path not in dataset_cache:

        dataset_cache[file_path] = xr.open_dataset(
            file_path
        )

    return dataset_cache[file_path]


# ============================================================
# EXTRACT RAINFALL
# ============================================================

dated_df = df[
    df["event_date"].notna()
].copy()

print(
    f"Rainfall extraction records: {len(dated_df):,}"
)

print()


for index, row in dated_df.iterrows():

    processed += 1

    sl_no = row["sl_no"]
    latitude = float(row["latitude"])
    longitude = float(row["longitude"])

    event_date = row["event_date"]

    date_string = event_date.strftime(
        "%Y-%m-%d"
    )

    print(
        f"[{processed}/{len(dated_df)}] "
        f"Sl.No {sl_no} | {date_string}",
        end="\r"
    )

    weather_file = find_weather_file(
        date_string
    )

    if weather_file is None:

        failed += 1

        rainfall_records.append({
            "sl_no": sl_no,
            "latitude": latitude,
            "longitude": longitude,
            "event_date": date_string,
            "rainfall_mm_day": np.nan,
            "rainfall_source": "missing"
        })

        continue

    try:

        ds = get_dataset(
            weather_file
        )

        # ----------------------------------------------------
        # Select nearest IMERG grid cell
        # ----------------------------------------------------

        point = ds["precipitation"].sel(
            lat=latitude,
            lon=longitude,
            method="nearest"
        )

        rainfall = float(
            point.values.squeeze()
        )

        if not np.isfinite(rainfall):
            rainfall = np.nan

        filename = os.path.basename(
            weather_file
        )

        if "3B-DAY-L." in filename:
            source = "IMERG_Late_V07"
        else:
            source = "IMERG_Final_V07"

        rainfall_records.append({
            "sl_no": sl_no,
            "latitude": latitude,
            "longitude": longitude,
            "event_date": date_string,
            "rainfall_mm_day": rainfall,
            "rainfall_source": source
        })

    except Exception as error:

        failed += 1

        rainfall_records.append({
            "sl_no": sl_no,
            "latitude": latitude,
            "longitude": longitude,
            "event_date": date_string,
            "rainfall_mm_day": np.nan,
            "rainfall_source": "error"
        })


print()
print()


# ============================================================
# CLOSE DATASETS
# ============================================================

for ds in dataset_cache.values():
    ds.close()


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

rainfall_df = pd.DataFrame(
    rainfall_records
)


# ============================================================
# SAVE OUTPUT
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

rainfall_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("=" * 70)
print("RAINFALL EXTRACTION COMPLETED")
print("=" * 70)
print()

print(
    f"Records with exact event date : {len(dated_df):,}"
)

print(
    f"Rainfall records created      : {len(rainfall_df):,}"
)

print(
    f"Processing errors             : {failed:,}"
)

print()

print("Rainfall source distribution:")

if len(rainfall_df) > 0:
    print(
        rainfall_df["rainfall_source"]
        .value_counts(dropna=False)
    )

print()

print("Missing rainfall values:")

if len(rainfall_df) > 0:
    print(
        rainfall_df["rainfall_mm_day"]
        .isna()
        .sum()
    )

print()

print("Rainfall range:")

if rainfall_df["rainfall_mm_day"].notna().any():

    print(
        "Minimum:",
        rainfall_df["rainfall_mm_day"].min()
    )

    print(
        "Maximum:",
        rainfall_df["rainfall_mm_day"].max()
    )

    print(
        "Mean:",
        rainfall_df["rainfall_mm_day"].mean()
    )

print()

print(
    f"Output file: {OUTPUT_FILE}"
)

print()
print("=" * 70)