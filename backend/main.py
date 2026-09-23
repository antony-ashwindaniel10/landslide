from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import math
import os
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import requests

from backend.dem_service import get_terrain_features
from backend.rainfall_service import get_rainfall
from backend.soil_moisture_service import get_soil_wetness
from backend.nasa_power_service import get_rainfall_and_soil
from backend.decision_service import (
    build_decision,
    build_heatmap,
    estimate_terrain,
    list_alerts,
    save_alert,
    save_report,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Landslide Digital Twin API",
    description="AI-Based Landslide Risk Monitoring System for North Eastern India",
    version="2.4.1"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "models",
    "landslide_risk_model_v2.pkl"
)


# ============================================================
# LOAD MACHINE LEARNING MODEL
# ============================================================

model = joblib.load(MODEL_PATH)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
    "rainfall_mm_day",
    "soil_wetness_gwet_top",
    "slope_degrees",
    "elevation_m",
    "latitude",
    "longitude"
]


# ============================================================
# RISK REQUEST
# ============================================================

class RiskRequest(BaseModel):

    latitude: float
    longitude: float

    # Automatic if not provided
    rainfall: float | None = None

    # Automatic if not provided
    soil_moisture: float | None = None

    slope: float
    elevation: float

    historical_landslide: bool = False


class ReportRequest(BaseModel):

    latitude: float
    longitude: float
    note: str = ""
    reporter: str = "Citizen"
    image_base64: str | None = None


class AlertRequest(BaseModel):

    latitude: float
    longitude: float
    place: str = "Selected slope"
    risk_level: str = "Yellow"
    risk_score: float = 0
    language: str = "en"
    channel: str = "SMS"


class PredictAtRequest(BaseModel):

    latitude: float
    longitude: float
    historical_landslide: bool = False
    # Optional overrides (manual recalculate with known terrain)
    slope: float | None = None
    elevation: float | None = None


def _fetch_open_meteo_forecast(latitude: float, longitude: float):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation",
            "forecast_days": 3,
            "timezone": "auto",
        },
        timeout=8,
    )
    response.raise_for_status()
    return response.json()


def _build_forecast_risk(
    latitude: float,
    longitude: float,
    slope: float,
    elevation: float,
    soil_wetness: float,
    weather_data: dict,
):
    times = weather_data["hourly"]["time"]
    rainfall_values = weather_data["hourly"]["precipitation"]

    daily_rainfall = {}
    for time_value, rainfall in zip(times, rainfall_values):
        date = time_value.split("T")[0]
        daily_rainfall[date] = daily_rainfall.get(date, 0.0) + (rainfall or 0.0)

    forecast_results = []
    for date, rainfall in daily_rainfall.items():
        input_data = pd.DataFrame(
            [[
                rainfall,
                soil_wetness,
                slope,
                elevation,
                latitude,
                longitude,
            ]],
            columns=FEATURES,
        )
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1]
        risk_score = round(probability * 100, 2)
        forecast_results.append({
            "date": date,
            "rainfall_mm": round(rainfall, 2),
            "landslide_probability": round(probability, 4),
            "risk_score": risk_score,
            "risk_level": get_risk_level(risk_score),
            "ml_prediction": int(prediction),
        })

    return {
        "latitude": latitude,
        "longitude": longitude,
        "soil_wetness_gwet_top": soil_wetness,
        "forecast_days": forecast_results,
        "source": "Open-Meteo + Random Forest Model",
    }


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Landslide Digital Twin API is running!",
        "version": "2.5.0-predict-at",
        "model": "landslide_risk_model_v2"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "model_loaded": True
    }


# ============================================================
# ELEVATION + SLOPE API
# ============================================================

@app.get("/elevation")
def elevation_api(
    latitude: float,
    longitude: float
):

    try:

        terrain = get_terrain_features(
            latitude,
            longitude
        )

        return {
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": round(
                terrain["elevation_m"],
                2
            ),
            "slope_degrees": round(
                terrain["slope_degrees"],
                2
            ),
            "source": "SRTM DEM"
        }

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Terrain calculation failed: {error}"
        )


# ============================================================
# PLACE NAME (REVERSE GEOCODING)
# ============================================================

@app.get("/place-name")
def place_name_api(
    latitude: float,
    longitude: float
):

    try:

        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "zoom": 14,
                "addressdetails": 1,
            },
            headers={
                "User-Agent": "LandslideDigitalTwin/2.4.1 (educational research)"
            },
            timeout=12,
        )

        response.raise_for_status()
        data = response.json()

        address = data.get("address") or {}

        # Prefer the most specific local place name available
        name_parts = [
            address.get("village"),
            address.get("town"),
            address.get("city"),
            address.get("suburb"),
            address.get("neighbourhood"),
            address.get("hamlet"),
            address.get("locality"),
            address.get("county"),
            address.get("state_district"),
            address.get("state"),
        ]

        local_name = next(
            (part for part in name_parts if part),
            None
        )

        region_parts = [
            address.get("state_district"),
            address.get("state"),
            address.get("country"),
        ]

        # Avoid repeating the same token twice
        unique_region = []
        for part in region_parts:
            if part and part != local_name and part not in unique_region:
                unique_region.append(part)

        if local_name and unique_region:
            place_name = f"{local_name}, {', '.join(unique_region)}"
        elif local_name:
            place_name = local_name
        else:
            place_name = data.get("display_name") or "Unknown location"

        return {
            "latitude": latitude,
            "longitude": longitude,
            "place_name": place_name,
            "display_name": data.get("display_name"),
            "address": address,
            "source": "OpenStreetMap Nominatim",
        }

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=f"Place name lookup failed: {error}"
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Place name lookup failed: {error}"
        )


# ============================================================
# RAINFALL API
# ============================================================

@app.get("/rainfall")
def rainfall_api(
    latitude: float,
    longitude: float
):

    try:

        rainfall = get_rainfall(
            latitude,
            longitude
        )

        return rainfall

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Rainfall retrieval failed: {error}"
        )


# ============================================================
# FUTURE RAINFALL FORECAST API
# ============================================================

@app.get("/forecast-rainfall")
def forecast_rainfall_api(
    latitude: float,
    longitude: float
):

    try:

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation",
            "forecast_days": 3,
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        weather_data = response.json()

        return {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_data.get(
                "timezone"
            ),
            "elevation_m": weather_data.get(
                "elevation"
            ),
            "forecast_days": 3,
            "hourly": {
                "time": weather_data[
                    "hourly"
                ]["time"],
                "precipitation_mm": weather_data[
                    "hourly"
                ]["precipitation"]
            },
            "source": "Open-Meteo"
        }

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "Rainfall forecast service failed: "
                f"{error}"
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Rainfall forecast retrieval failed: "
                f"{error}"
            )
        )


# ============================================================
# FORECAST-BASED LANDSLIDE RISK API
# ============================================================

@app.get("/forecast-risk")
def forecast_risk_api(
    latitude: float,
    longitude: float,
    slope: float,
    elevation: float,
    soil_wetness: float
):

    try:

        # ====================================================
        # 1. GET 3-DAY RAINFALL FORECAST
        # ====================================================

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation",
            "forecast_days": 3,
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        weather_data = response.json()


        # ====================================================
        # 2. GET HOURLY FORECAST DATA
        # ====================================================

        times = weather_data[
            "hourly"
        ]["time"]

        rainfall_values = weather_data[
            "hourly"
        ]["precipitation"]


        # ====================================================
        # 3. CONVERT HOURLY RAINFALL TO DAILY TOTALS
        # ====================================================

        daily_rainfall = {}

        for time_value, rainfall in zip(
            times,
            rainfall_values
        ):

            date = time_value.split("T")[0]

            if date not in daily_rainfall:

                daily_rainfall[date] = 0.0

            daily_rainfall[date] += (
                rainfall or 0.0
            )


        # ====================================================
        # 4. CALCULATE RISK FOR EACH FORECAST DAY
        # ====================================================

        forecast_results = []

        for date, rainfall in daily_rainfall.items():

            # ------------------------------------------------
            # Prepare input using the exact ML features
            # ------------------------------------------------

            input_data = pd.DataFrame(
                [[
                    rainfall,
                    soil_wetness,
                    slope,
                    elevation,
                    latitude,
                    longitude
                ]],
                columns=FEATURES
            )


            # ------------------------------------------------
            # ML prediction
            # ------------------------------------------------

            prediction = model.predict(
                input_data
            )[0]

            probability = model.predict_proba(
                input_data
            )[0][1]


            # ------------------------------------------------
            # Risk score
            # ------------------------------------------------

            risk_score = round(
                probability * 100,
                2
            )

            risk_level = get_risk_level(
                risk_score
            )


            # ------------------------------------------------
            # Store daily result
            # ------------------------------------------------

            forecast_results.append({

                "date": date,

                "rainfall_mm": round(
                    rainfall,
                    2
                ),

                "risk_score": risk_score,

                "risk_level": risk_level,

                "ml_prediction": int(
                    prediction
                ),

                "landslide_probability": round(
                    probability,
                    4
                )
            })


        # ====================================================
        # 5. RETURN FORECAST RISK
        # ====================================================

        return {

            "location": {

                "latitude": latitude,

                "longitude": longitude
            },

            "terrain": {

                "slope_degrees": slope,

                "elevation_m": elevation
            },

            "soil_wetness": soil_wetness,

            "forecast_days": forecast_results,

            "source": (
                "Open-Meteo rainfall forecast + "
                "Landslide Random Forest Model"
            )
        }


    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "Rainfall forecast service failed: "
                f"{error}"
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Forecast risk calculation failed: "
                f"{error}"
            )
        )


# ============================================================
# SOIL WETNESS API
# ============================================================

@app.get("/soil-wetness")
def soil_wetness_api(
    latitude: float,
    longitude: float
):

    try:

        soil = get_soil_wetness(
            latitude,
            longitude
        )

        return soil

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Soil wetness retrieval failed: {error}"
        )


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(risk_score):

    if risk_score >= 75:
        return "Red"

    elif risk_score >= 50:
        return "Orange"

    elif risk_score >= 25:
        return "Yellow"

    else:
        return "Green"


# ============================================================
# AI RISK PREDICTION
# ============================================================

@app.post("/risk")
def calculate_risk(data: RiskRequest):

    # ========================================================
    # AUTOMATIC RAINFALL + SOIL WETNESS (parallel when both needed)
    # ========================================================

    rainfall_source = "User Input"
    rainfall_date = None
    soil_source = "User Input"
    soil_date = None

    need_rainfall = data.rainfall is None
    need_soil = data.soil_moisture is None

    rainfall = data.rainfall
    soil_wetness = data.soil_moisture

    try:
        if need_rainfall and need_soil:
            weather = get_rainfall_and_soil(
                data.latitude,
                data.longitude,
            )
            rainfall = weather["rainfall_mm_day"]
            rainfall_date = weather["rainfall_date"]
            rainfall_source = weather["rainfall_source"]
            soil_wetness = weather["soil_wetness"]
            soil_date = weather["soil_wetness_date"]
            soil_source = weather["soil_wetness_source"]

        elif need_rainfall:
            rainfall_result = get_rainfall(data.latitude, data.longitude)
            rainfall = rainfall_result["rainfall_mm_day"]
            rainfall_date = rainfall_result["date"]
            rainfall_source = rainfall_result["source"]

        elif need_soil:
            soil_result = get_soil_wetness(data.latitude, data.longitude)
            soil_wetness = soil_result["soil_wetness"]
            soil_date = soil_result["date"]
            soil_source = soil_result["source"]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Automatic weather retrieval failed: {error}",
        ) from error


    # ========================================================
    # PREPARE ML INPUT
    # ========================================================

    input_data = pd.DataFrame(
        [[
            rainfall,
            soil_wetness,
            data.slope,
            data.elevation,
            data.latitude,
            data.longitude
        ]],
        columns=FEATURES
    )


    # ========================================================
    # MACHINE LEARNING PREDICTION
    # ========================================================

    prediction = model.predict(
        input_data
    )[0]

    probability = model.predict_proba(
        input_data
    )[0][1]


    # ========================================================
    # RISK SCORE
    # ========================================================

    risk_score = round(
        probability * 100,
        2
    )

    risk_level = get_risk_level(
        risk_score
    )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "location": {

            "latitude": data.latitude,

            "longitude": data.longitude
        },

        "environment": {

            "rainfall_mm_day": rainfall,

            "rainfall_date": rainfall_date,

            "rainfall_source": rainfall_source,

            "soil_wetness_gwet_top": soil_wetness,

            "soil_wetness_date": soil_date,

            "soil_wetness_source": soil_source,

            "slope_degrees": data.slope,

            "elevation_m": data.elevation,

            "historical_landslide":
                data.historical_landslide
        },

        "prediction": {

            "ml_prediction": int(
                prediction
            ),

            "landslide_probability": round(
                probability,
                4
            ),

            "risk_score": risk_score,

            "risk_level": risk_level
        }
    }


# ============================================================
# FAST COMBINED PREDICTION (terrain + weather + forecast)
# ============================================================

@app.post("/predict-at")
def predict_at(data: PredictAtRequest):

    latitude = data.latitude
    longitude = data.longitude
    terrain_source = "SRTM DEM"

    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            weather_future = pool.submit(
                get_rainfall_and_soil, latitude, longitude
            )
            forecast_future = pool.submit(
                _fetch_open_meteo_forecast, latitude, longitude
            )

            if data.slope is None or data.elevation is None:
                try:
                    terrain = get_terrain_features(latitude, longitude)
                    elevation = float(terrain["elevation_m"])
                    slope = float(terrain["slope_degrees"])
                    if (
                        not math.isfinite(elevation)
                        or not math.isfinite(slope)
                        or elevation < -500
                    ):
                        raise ValueError("DEM sample is empty")
                except Exception:
                    estimated = estimate_terrain(latitude, longitude)
                    elevation = estimated["elevation_m"]
                    slope = estimated["slope_degrees"]
                    terrain_source = estimated["source"]
            else:
                elevation = float(data.elevation)
                slope = float(data.slope)
                terrain_source = "Provided"

            try:
                weather = weather_future.result()
            except Exception:
                weather = {
                    "rainfall_mm_day": 0.0,
                    "rainfall_date": None,
                    "rainfall_source": "Unavailable",
                    "soil_wetness": 0.8,
                    "soil_wetness_date": None,
                    "soil_wetness_source": "Unavailable",
                }

            try:
                weather_data = forecast_future.result()
            except Exception:
                weather_data = None

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Location prediction failed: {error}",
        ) from error

    rainfall = float(weather["rainfall_mm_day"])
    soil_wetness = float(weather["soil_wetness"])
    elevation = float(elevation)
    slope = float(slope)

    input_data = pd.DataFrame(
        [[
            rainfall,
            soil_wetness,
            slope,
            elevation,
            latitude,
            longitude,
        ]],
        columns=FEATURES,
    )

    prediction = model.predict(input_data)[0]
    probability = float(model.predict_proba(input_data)[0][1])
    risk_score = round(probability * 100, 2)
    risk_level = get_risk_level(risk_score)

    forecast_risk = None
    forecast_rainfall = None
    if weather_data and weather_data.get("hourly"):
        forecast_risk = _build_forecast_risk(
            latitude,
            longitude,
            slope,
            elevation,
            soil_wetness,
            weather_data,
        )
        forecast_rainfall = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_data.get("timezone"),
            "elevation_m": weather_data.get("elevation"),
            "forecast_days": 3,
            "hourly": {
                "time": weather_data["hourly"]["time"],
                "precipitation_mm": weather_data["hourly"]["precipitation"],
            },
            "source": "Open-Meteo",
        }

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "environment": {
            "rainfall_mm_day": rainfall,
            "rainfall_date": weather["rainfall_date"],
            "rainfall_source": weather["rainfall_source"],
            "soil_wetness_gwet_top": soil_wetness,
            "soil_wetness_date": weather["soil_wetness_date"],
            "soil_wetness_source": weather["soil_wetness_source"],
            "slope_degrees": round(slope, 2),
            "elevation_m": round(elevation, 2),
            "terrain_source": terrain_source,
            "historical_landslide": data.historical_landslide,
        },
        "prediction": {
            "ml_prediction": int(prediction),
            "landslide_probability": round(probability, 4),
            "risk_score": float(risk_score),
            "risk_level": risk_level,
        },
        "forecast_rainfall": forecast_rainfall,
        "forecast_risk": forecast_risk,
    }


# ============================================================
# HEATMAP, DECISION SUPPORT, REPORTS, ALERTS
# ============================================================

@app.get("/heatmap")
def heatmap_api():

    return {
        "cells": build_heatmap(),
        "source": "GSI historical inventory, gridded susceptibility",
    }


@app.get("/decision")
def decision_api(
    latitude: float,
    longitude: float,
    ml_score: float = 0,
    rainfall_mm: float = 0,
    soil_wetness: float = 0,
    slope: float = 0,
    forecast_rain_72h: float = 0,
    place_name: str = "",
):

    return build_decision(
        latitude,
        longitude,
        ml_score,
        rainfall_mm,
        soil_wetness,
        slope,
        forecast_rain_72h,
        place_name,
    )


@app.post("/reports")
def reports_api(data: ReportRequest):

    image_bytes = None
    if data.image_base64:
        import base64
        try:
            payload = data.image_base64.split(",")[-1]
            image_bytes = base64.b64decode(payload)
        except Exception:
            image_bytes = None

    return save_report(
        data.latitude,
        data.longitude,
        data.note,
        data.reporter,
        image_bytes,
    )


@app.post("/alerts")
def alerts_api(data: AlertRequest):

    return save_alert(
        data.latitude,
        data.longitude,
        data.place,
        data.risk_level,
        data.risk_score,
        data.language,
        data.channel,
    )


@app.get("/alerts")
def alerts_list_api():

    return {"alerts": list_alerts()}