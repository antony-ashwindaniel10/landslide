# ============================================================
# LANDSLIDE DYNAMIC RISK SCORING ENGINE
# ============================================================

import joblib
import pandas as pd


# ============================================================
# MODEL
# ============================================================

MODEL_FILE = "ml/models/landslide_risk_model_v2.pkl"


# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(MODEL_FILE)


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
# RISK LEVEL FUNCTION
# ============================================================

def get_risk_level(risk_score):

    if risk_score < 25:
        return "GREEN"

    elif risk_score < 50:
        return "YELLOW"

    elif risk_score < 75:
        return "ORANGE"

    else:
        return "RED"


# ============================================================
# MAIN RISK FUNCTION
# ============================================================

def calculate_risk(
    rainfall_mm_day,
    soil_wetness_gwet_top,
    slope_degrees,
    elevation_m,
    latitude,
    longitude
):

    # --------------------------------------------------------
    # Create DataFrame with the exact model feature names
    # --------------------------------------------------------

    features = pd.DataFrame([{
        "rainfall_mm_day": rainfall_mm_day,
        "soil_wetness_gwet_top": soil_wetness_gwet_top,
        "slope_degrees": slope_degrees,
        "elevation_m": elevation_m,
        "latitude": latitude,
        "longitude": longitude
    }])


    # --------------------------------------------------------
    # Make sure feature order is exactly correct
    # --------------------------------------------------------

    features = features[FEATURES]


    # --------------------------------------------------------
    # Get landslide probability
    # --------------------------------------------------------

    probability = model.predict_proba(
        features
    )[0][1]


    # --------------------------------------------------------
    # Convert probability to 0-100 risk score
    # --------------------------------------------------------

    risk_score = probability * 100


    # --------------------------------------------------------
    # Determine risk level
    # --------------------------------------------------------

    risk_level = get_risk_level(
        risk_score
    )


    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "risk_score": round(
            float(risk_score),
            2
        ),

        "risk_level": risk_level,

        "landslide_probability": round(
            float(probability),
            4
        )
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("LANDSLIDE RISK ENGINE TEST")
    print("=" * 60)


    # --------------------------------------------------------
    # Example location and environmental conditions
    # --------------------------------------------------------

    latitude = 27.4728
    longitude = 94.9120

    rainfall = 120
    soil_wetness = 0.95
    slope = 35
    elevation = 1200


    print("\nInput conditions:")

    print(
        "Latitude:",
        latitude
    )

    print(
        "Longitude:",
        longitude
    )

    print(
        "Rainfall:",
        rainfall,
        "mm/day"
    )

    print(
        "Soil wetness:",
        soil_wetness
    )

    print(
        "Slope:",
        slope,
        "degrees"
    )

    print(
        "Elevation:",
        elevation,
        "m"
    )


    # --------------------------------------------------------
    # Calculate risk
    # --------------------------------------------------------

    result = calculate_risk(
        rainfall_mm_day=rainfall,
        soil_wetness_gwet_top=soil_wetness,
        slope_degrees=slope,
        elevation_m=elevation,
        latitude=latitude,
        longitude=longitude
    )


    # --------------------------------------------------------
    # Display result
    # --------------------------------------------------------

    print("\nAI prediction:")

    print(
        "Landslide probability:",
        result["landslide_probability"]
    )

    print(
        "Risk score:",
        result["risk_score"],
        "/ 100"
    )

    print(
        "Risk level:",
        result["risk_level"]
    )


    print("\n" + "=" * 60)
    print("RISK ENGINE TEST COMPLETE")
    print("=" * 60)