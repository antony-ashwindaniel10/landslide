import pandas as pd
import requests
import time

# ============================================================
# NASA POWER SOIL WETNESS EXTRACTION
# ============================================================

INPUT_FILE = "data/processed/event_rainfall_features.csv"
OUTPUT_FILE = "data/processed/event_soil_moisture_power.csv"

# NASA POWER parameter
PARAMETER = "GWETTOP"

# Load event records
df = pd.read_csv(INPUT_FILE)

print("=" * 70)
print("NASA POWER SOIL WETNESS EXTRACTION")
print("=" * 70)
print(f"Input records: {len(df)}")
print()

results = []

for index, row in df.iterrows():

    latitude = float(row["latitude"])
    longitude = float(row["longitude"])
    event_date = str(row["event_date"])

    date_clean = event_date.replace("-", "")

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters={PARAMETER}"
        f"&community=AG"
        f"&longitude={longitude}"
        f"&latitude={latitude}"
        f"&start={date_clean}"
        f"&end={date_clean}"
        f"&format=JSON"
    )

    soil_wetness = None
    source = None

    try:

        response = requests.get(url, timeout=30)

        if response.status_code == 200:

            data = response.json()

            value = data["properties"]["parameter"][PARAMETER].get(
                date_clean
            )

            if value is not None and value != -999:

                soil_wetness = float(value)
                source = "NASA_POWER_MERRA2"

        else:

            print(
                f"API error | Record {index + 1} | "
                f"HTTP {response.status_code}"
            )

    except Exception as e:

        print(
            f"Error | Record {index + 1} | "
            f"{event_date} | {e}"
        )

    results.append(
        {
            "latitude": latitude,
            "longitude": longitude,
            "event_date": event_date,
            "soil_wetness_gwet_top": soil_wetness,
            "soil_moisture_source": source,
        }
    )

    # Progress display
    if (index + 1) % 50 == 0 or index + 1 == len(df):

        successful = sum(
            r["soil_wetness_gwet_top"] is not None
            for r in results
        )

        print(
            f"Processed {index + 1}/{len(df)} | "
            f"Successful: {successful}"
        )

    # Small delay to avoid sending requests too quickly
    time.sleep(0.1)


# ============================================================
# SAVE RESULTS
# ============================================================

result_df = pd.DataFrame(results)

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ============================================================
# SUMMARY
# ============================================================

successful = result_df[
    "soil_wetness_gwet_top"
].notna().sum()

failed = result_df[
    "soil_wetness_gwet_top"
].isna().sum()

print()
print("=" * 70)
print("NASA POWER EXTRACTION COMPLETE")
print("=" * 70)

print(f"Total records : {len(result_df)}")
print(f"Successful    : {successful}")
print(f"Failed        : {failed}")

if successful > 0:

    print()
    print("Soil wetness statistics:")
    print(
        f"Minimum : "
        f"{result_df['soil_wetness_gwet_top'].min():.4f}"
    )
    print(
        f"Maximum : "
        f"{result_df['soil_wetness_gwet_top'].max():.4f}"
    )
    print(
        f"Mean    : "
        f"{result_df['soil_wetness_gwet_top'].mean():.4f}"
    )

print()
print(f"Output file:")
print(OUTPUT_FILE)
print("=" * 70)