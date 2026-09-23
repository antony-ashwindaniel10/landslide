import pandas as pd
import requests

# Load the 280 event dates
df = pd.read_csv("data/processed/event_rainfall_features.csv")

dates = sorted(
    df["event_date"].astype(str).unique()
)

lat = 24.0
lon = 92.85

successful = []
failed = []

print(f"Testing {len(dates)} event dates...")

for date in dates:
    date_clean = date.replace("-", "")

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=GWETTOP"
        f"&community=AG"
        f"&longitude={lon}"
        f"&latitude={lat}"
        f"&start={date_clean}"
        f"&end={date_clean}"
        f"&format=JSON"
    )

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()

            value = data["properties"]["parameter"]["GWETTOP"].get(
                date_clean
            )

            if value is not None and value != -999:
                successful.append(date)
            else:
                failed.append(date)

        else:
            failed.append(date)

    except Exception as e:
        print(f"Error for {date}: {e}")
        failed.append(date)


print()
print("=" * 60)
print("NASA POWER COVERAGE TEST")
print("=" * 60)
print(f"Total dates tested : {len(dates)}")
print(f"Successful         : {len(successful)}")
print(f"Failed             : {len(failed)}")

print()
print("Failed dates:")
for date in failed:
    print(date)