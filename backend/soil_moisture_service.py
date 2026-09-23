# ============================================================
# AUTOMATIC SOIL WETNESS SERVICE
# NASA POWER / MERRA-2
# ============================================================

import requests
from datetime import datetime, timedelta


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)


def get_soil_wetness(latitude: float, longitude: float):
    """
    Get the latest available surface soil wetness
    using NASA POWER MERRA-2 GWETTOP parameter.

    GWETTOP:
    Surface soil wetness index, approximately 0 to 1.
    """

    today = datetime.utcnow().date()

    # NASA POWER data can have a short delay,
    # so check the previous 7 days.
    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=1)

    params = {
        "parameters": "GWETTOP",
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

    soil_data = (
        data
        .get("properties", {})
        .get("parameter", {})
        .get("GWETTOP", {})
    )

    if not soil_data:
        raise ValueError(
            "No soil wetness data returned by NASA POWER."
        )

    valid_values = []

    for date_string, value in soil_data.items():

        try:
            soil_wetness = float(value)

            if 0 <= soil_wetness <= 1:
                valid_values.append(
                    (date_string, soil_wetness)
                )

        except (ValueError, TypeError):
            continue

    if not valid_values:
        raise ValueError(
            "No valid soil wetness value found."
        )

    latest_date, soil_wetness = max(
        valid_values,
        key=lambda x: x[0]
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "soil_wetness": round(soil_wetness, 4),
        "date": latest_date,
        "source": "NASA POWER MERRA-2 GWETTOP",
    }