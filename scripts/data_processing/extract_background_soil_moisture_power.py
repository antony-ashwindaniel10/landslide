import pandas as pd
import requests
import time

# ============================================================
# FILES
# ============================================================

INPUT_FILE = "data/processed/background_event_dates.csv"

OUTPUT_FILE = "data/processed/background_soil_moisture_power.csv"


# ============================================================
# NASA POWER API
# ============================================================

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("NASA POWER BACKGROUND SOIL WETNESS EXTRACTION")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"Input records: {len(df)}")


# ============================================================
# EXTRACT SOIL WETNESS
# ============================================================

results = []

successful = 0
failed = 0

for index, row in df.iterrows():

    latitude = float(row["latitude"])
    longitude = float(row["longitude"])

    event_date = pd.to_datetime(row["event_date"]).strftime("%Y%m%d")

    params = {
        "parameters": "GWETTOP",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": event_date,
        "end": event_date,
        "format": "JSON"
    }

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        value = data["properties"]["parameter"]["GWETTOP"][event_date]

        results.append({
            "latitude": latitude,
            "longitude": longitude,
            "event_date": pd.to_datetime(row["event_date"]).strftime("%Y-%m-%d"),
            "soil_wetness_gwet_top": float(value),
            "soil_moisture_source": "NASA_POWER_MERRA2"
        })

        successful += 1

    except Exception as e:

        print(
            f"\nFailed record {index + 1}: "
            f"lat={latitude}, lon={longitude}, date={event_date}"
        )

        print(f"Error: {e}")

        failed += 1

        results.append({
            "latitude": latitude,
            "longitude": longitude,
            "event_date": pd.to_datetime(row["event_date"]).strftime("%Y-%m-%d"),
            "soil_wetness_gwet_top": None,
            "soil_moisture_source": "FAILED"
        })

    if (index + 1) % 50 == 0 or (index + 1) == len(df):

        print(
            f"Processed {index + 1}/{len(df)} | "
            f"Successful: {successful} | "
            f"Failed: {failed}"
        )

    # Small delay to avoid sending requests too quickly
    time.sleep(0.1)


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

output_df = pd.DataFrame(results)


# ============================================================
# SAVE
# ============================================================

output_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("NASA POWER BACKGROUND SOIL WETNESS EXTRACTION COMPLETE")
print("=" * 70)

print(f"Total records : {len(output_df)}")
print(f"Successful    : {successful}")
print(f"Failed        : {failed}")

if successful > 0:

    valid_values = output_df[
        output_df["soil_wetness_gwet_top"].notna()
    ]["soil_wetness_gwet_top"]

    print("\nSoil wetness statistics:")

    print(
        f"Minimum : {valid_values.min():.4f}"
    )

    print(
        f"Maximum : {valid_values.max():.4f}"
    )

    print(
        f"Mean    : {valid_values.mean():.4f}"
    )

print("\nOutput file:")
print(OUTPUT_FILE)

print("=" * 70)