import os
import re
import pandas as pd
import xarray as xr


# ============================================================
# FILE PATHS
# ============================================================

BACKGROUND_DATES_FILE = "data/processed/background_event_dates.csv"
WEATHER_DIR = "data/weather"
OUTPUT_FILE = "data/processed/background_rainfall_features.csv"


# ============================================================
# CHECK INPUT FILES
# ============================================================

if not os.path.exists(BACKGROUND_DATES_FILE):
    print("ERROR: Background event dates file not found.")
    print(f"Expected: {BACKGROUND_DATES_FILE}")
    raise SystemExit

if not os.path.exists(WEATHER_DIR):
    print("ERROR: Weather directory not found.")
    print(f"Expected: {WEATHER_DIR}")
    raise SystemExit


# ============================================================
# LOAD BACKGROUND EVENT DATA
# ============================================================

background = pd.read_csv(BACKGROUND_DATES_FILE)

print("=" * 70)
print("BACKGROUND IMERG RAINFALL EXTRACTION")
print("=" * 70)
print()

print(f"Background records: {len(background):,}")
print()


# ============================================================
# INDEX IMERG NETCDF FILES
# ============================================================

print("Indexing IMERG files...")

weather_files = {}

for filename in os.listdir(WEATHER_DIR):

    if not filename.lower().endswith(".nc4"):
        continue

    # --------------------------------------------------------
    # Expected filenames:
    #
    # Final:
    # 3B-DAY.MS.MRG.3IMERG.20240528-S000000-E235959.V07B.nc4
    #
    # Late:
    # 3B-DAY-L.MS.MRG.3IMERG.20260530-S000000-E235959.V07C.nc4
    #
    # Extract the YYYYMMDD immediately after "3IMERG."
    # --------------------------------------------------------

    match = re.search(
        r"3IMERG\.(\d{8})-",
        filename
    )

    if not match:
        continue

    date_raw = match.group(1)

    date = (
        date_raw[0:4]
        + "-"
        + date_raw[4:6]
        + "-"
        + date_raw[6:8]
    )

    # --------------------------------------------------------
    # Prefer Final Run over Late Run
    # --------------------------------------------------------

    if date not in weather_files:

        weather_files[date] = filename

    else:

        # Final filename contains:
        # 3B-DAY.MS.MRG.3IMERG.
        #
        # Late filename contains:
        # 3B-DAY-L.MS.MRG.3IMERG.

        if "3B-DAY.MS.MRG.3IMERG." in filename:

            weather_files[date] = filename


print(f"IMERG files indexed: {len(weather_files):,}")
print()


# ============================================================
# WEATHER DATASET CACHE
# ============================================================

dataset_cache = {}


def get_dataset(date):
    """
    Open and cache the IMERG NetCDF dataset for a date.
    """

    if date in dataset_cache:
        return dataset_cache[date]

    if date not in weather_files:
        return None

    filename = weather_files[date]

    filepath = os.path.join(
        WEATHER_DIR,
        filename
    )

    try:

        ds = xr.open_dataset(filepath)

        dataset_cache[date] = ds

        return ds

    except Exception as error:

        print()
        print(f"ERROR opening weather file:")
        print(filename)
        print(f"Error: {error}")

        return None


# ============================================================
# EXTRACT RAINFALL
# ============================================================

results = []

errors = 0
missing_files = 0
missing_values = 0


print("Extracting rainfall...")
print()


for index, row in background.iterrows():

    latitude = float(row["latitude"])

    longitude = float(row["longitude"])

    event_date = str(row["event_date"])


    # --------------------------------------------------------
    # Progress display
    # --------------------------------------------------------

    if (
        index % 50 == 0
        or index == len(background) - 1
    ):

        print(
            f"[{index + 1}/{len(background)}] "
            f"Lat {latitude:.6f} | "
            f"Lon {longitude:.6f} | "
            f"{event_date}"
        )


    # --------------------------------------------------------
    # FIND WEATHER FILE
    # --------------------------------------------------------

    if event_date not in weather_files:

        missing_files += 1

        results.append({

            "latitude": latitude,

            "longitude": longitude,

            "event_date": event_date,

            "rainfall_mm_day": None,

            "rainfall_source": "missing"

        })

        continue


    # --------------------------------------------------------
    # OPEN IMERG DATASET
    # --------------------------------------------------------

    ds = get_dataset(event_date)

    if ds is None:

        errors += 1

        results.append({

            "latitude": latitude,

            "longitude": longitude,

            "event_date": event_date,

            "rainfall_mm_day": None,

            "rainfall_source": "error"

        })

        continue


    # --------------------------------------------------------
    # EXTRACT NEAREST IMERG PIXEL
    # --------------------------------------------------------

    try:

        rainfall = ds["precipitation"].sel(

            lat=latitude,

            lon=longitude,

            method="nearest"

        ).values


        # Remove the time dimension
        rainfall_value = float(
            rainfall.squeeze()
        )


        # ----------------------------------------------------
        # DETECT IMERG SOURCE
        # ----------------------------------------------------

        filename = weather_files[event_date]

        if "3B-DAY-L." in filename:

            source = "IMERG_Late_V07"

        else:

            source = "IMERG_Final_V07"


        # ----------------------------------------------------
        # CHECK FOR NaN
        # ----------------------------------------------------

        if pd.isna(rainfall_value):

            missing_values += 1

            rainfall_value = None

            source = "missing"


        # ----------------------------------------------------
        # SAVE RESULT
        # ----------------------------------------------------

        results.append({

            "latitude": latitude,

            "longitude": longitude,

            "event_date": event_date,

            "rainfall_mm_day": rainfall_value,

            "rainfall_source": source

        })


    except Exception as error:

        errors += 1

        results.append({

            "latitude": latitude,

            "longitude": longitude,

            "event_date": event_date,

            "rainfall_mm_day": None,

            "rainfall_source": "error"

        })


# ============================================================
# CLOSE ALL OPEN DATASETS
# ============================================================

for ds in dataset_cache.values():

    try:

        ds.close()

    except Exception:

        pass


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

rainfall_df = pd.DataFrame(results)


# ============================================================
# SAVE OUTPUT FILE
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

print()

print("=" * 70)
print("BACKGROUND RAINFALL EXTRACTION COMPLETED")
print("=" * 70)
print()


print(
    f"Background records processed : "
    f"{len(background):,}"
)


print(
    f"Rainfall records created     : "
    f"{len(rainfall_df):,}"
)


print(
    f"Processing errors            : "
    f"{errors:,}"
)


print(
    f"Missing weather files        : "
    f"{missing_files:,}"
)


print(
    f"Missing rainfall values      : "
    f"{missing_values:,}"
)


print()


# ============================================================
# SOURCE DISTRIBUTION
# ============================================================

print("Rainfall source distribution:")

print(
    rainfall_df["rainfall_source"].value_counts()
)


print()


# ============================================================
# RAINFALL STATISTICS
# ============================================================

valid_rainfall = rainfall_df[
    rainfall_df["rainfall_mm_day"].notna()
]["rainfall_mm_day"]


if len(valid_rainfall) > 0:

    print("Rainfall range:")

    print(
        f"Minimum: "
        f"{valid_rainfall.min():.6f} mm/day"
    )

    print(
        f"Maximum: "
        f"{valid_rainfall.max():.6f} mm/day"
    )

    print(
        f"Mean   : "
        f"{valid_rainfall.mean():.6f} mm/day"
    )

else:

    print("No valid rainfall values found.")


print()


# ============================================================
# OUTPUT
# ============================================================

print("Output file:")

print(OUTPUT_FILE)


print()

print("=" * 70)
print("COMPLETED")
print("=" * 70)