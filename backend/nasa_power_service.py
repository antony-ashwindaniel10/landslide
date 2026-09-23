# ============================================================
# NASA POWER — rainfall + soil wetness in one HTTP request
# ============================================================

import time
import requests
from datetime import datetime, timedelta


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)

_SESSION = requests.Session()
_CACHE = {}
_CACHE_TTL_SECONDS = 600  # 10 minutes


def _cache_key(latitude: float, longitude: float) -> str:
    return f"{round(latitude, 3)}:{round(longitude, 3)}"


def get_rainfall_and_soil(latitude: float, longitude: float):
    """
    Fetch PRECTOTCORR + GWETTOP together (one NASA POWER call).
    """

    key = _cache_key(latitude, longitude)
    cached = _CACHE.get(key)
    now = time.time()

    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=1)

    params = {
        "parameters": "PRECTOTCORR,GWETTOP",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }

    response = _SESSION.get(
        NASA_POWER_URL,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    parameters = (
        data
        .get("properties", {})
        .get("parameter", {})
    )

    rainfall_data = parameters.get("PRECTOTCORR", {})
    soil_data = parameters.get("GWETTOP", {})

    if not rainfall_data:
        raise ValueError("No rainfall data returned by NASA POWER.")

    if not soil_data:
        raise ValueError("No soil wetness data returned by NASA POWER.")

    rainfall_values = []
    for date_string, value in rainfall_data.items():
        try:
            rainfall = float(value)
            if rainfall >= 0:
                rainfall_values.append((date_string, rainfall))
        except (ValueError, TypeError):
            continue

    soil_values = []
    for date_string, value in soil_data.items():
        try:
            soil_wetness = float(value)
            if 0 <= soil_wetness <= 1:
                soil_values.append((date_string, soil_wetness))
        except (ValueError, TypeError):
            continue

    if not rainfall_values:
        raise ValueError("No valid rainfall value found.")

    if not soil_values:
        raise ValueError("No valid soil wetness value found.")

    latest_rain_date, rainfall = max(rainfall_values, key=lambda x: x[0])
    latest_soil_date, soil_wetness = max(soil_values, key=lambda x: x[0])

    result = {
        "latitude": latitude,
        "longitude": longitude,
        "rainfall_mm_day": round(rainfall, 2),
        "rainfall_date": latest_rain_date,
        "rainfall_source": "NASA POWER PRECTOTCORR",
        "soil_wetness": round(soil_wetness, 4),
        "soil_wetness_date": latest_soil_date,
        "soil_wetness_source": "NASA POWER MERRA-2 GWETTOP",
    }

    _CACHE[key] = (now, result)
    return result
