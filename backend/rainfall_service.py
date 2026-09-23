# ============================================================
# AUTOMATIC RAINFALL SERVICE
# NASA POWER Daily Precipitation
# ============================================================

import requests
from datetime import datetime, timedelta


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)


def get_rainfall(latitude: float, longitude: float):
    """
    Get the latest available daily rainfall
    for a latitude/longitude using NASA POWER.
    """

    # NASA POWER may have a small processing delay.
    # We request the previous few days and use
    # the latest available value.
    today = datetime.utcnow().date()

    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=1)

    params = {
        "parameters": "PRECTOTCORR",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }

    response = requests.get(
        NASA_POWER_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    rainfall_data = (
        data
        .get("properties", {})
        .get("parameter", {})
        .get("PRECTOTCORR", {})
    )

    if not rainfall_data:
        raise ValueError("No rainfall data returned by NASA POWER.")

    # Find the latest valid rainfall value
    valid_values = []

    for date_string, value in rainfall_data.items():

        try:
            rainfall = float(value)

            # NASA POWER uses -999 as missing value
            if rainfall >= 0:
                valid_values.append(
                    (date_string, rainfall)
                )

        except (ValueError, TypeError):
            continue

    if not valid_values:
        raise ValueError("No valid rainfall value found.")

    # Latest available date
    latest_date, rainfall = max(
        valid_values,
        key=lambda x: x[0]
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "rainfall_mm_day": round(rainfall, 2),
        "date": latest_date,
        "source": "NASA POWER PRECTOTCORR",
    }