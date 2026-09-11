import joblib
import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "model"
    / "landslide_susceptibility_model.pkl"
)


# ============================================================
# LOAD MODEL
# ============================================================

MODEL = joblib.load(MODEL_PATH)


FEATURE_COLUMNS = [
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos"
]


# ============================================================
# RAINFALL TRIGGER
# ============================================================

def rainfall_trigger(rainfall_24h, rainfall_7d):

    r24 = np.clip(
        rainfall_24h / 200.0,
        0,
        1
    )

    r7 = np.clip(
        rainfall_7d / 700.0,
        0,
        1
    )

    score = (
        0.60 * r24 +
        0.40 * r7
    ) * 100

    return round(float(score), 2)


# ============================================================
# SOIL MOISTURE TRIGGER
# ============================================================

def soil_moisture_trigger(soil_moisture):

    score = np.clip(
        (soil_moisture - 35.0) / 60.0,
        0,
        1
    ) * 100

    return round(float(score), 2)


# ============================================================
# ASPECT FEATURES
# ============================================================

def aspect_features(aspect_deg):

    radians = np.radians(aspect_deg)

    return (
        np.sin(radians),
        np.cos(radians)
    )


# ============================================================
# AI SUSCEPTIBILITY
# ============================================================

def calculate_susceptibility(
    elevation_m,
    slope_deg,
    aspect_deg
):

    aspect_sin, aspect_cos = aspect_features(
        aspect_deg
    )

    X = pd.DataFrame(
        [[
            elevation_m,
            slope_deg,
            aspect_sin,
            aspect_cos
        ]],
        columns=FEATURE_COLUMNS
    )

    raw_probability = (
        MODEL.predict_proba(X)[0][1] * 100
    )

    raw_probability = np.clip(
        raw_probability,
        0,
        100
    )

    # Calibration to prevent saturation
    calibrated = (
        100 *
        (raw_probability / 100) ** 2.8
    )

    return round(
        float(calibrated),
        2
    )


# ============================================================
# FINAL RISK
# ============================================================

def calculate_risk(
    elevation_m,
    slope_deg,
    aspect_deg,
    rainfall_24h,
    rainfall_7d,
    soil_moisture
):

    susceptibility = calculate_susceptibility(
        elevation_m,
        slope_deg,
        aspect_deg
    )

    rainfall = rainfall_trigger(
        rainfall_24h,
        rainfall_7d
    )

    soil = soil_moisture_trigger(
        soil_moisture
    )

    final_risk = (
        0.55 * susceptibility +
        0.30 * rainfall +
        0.15 * soil
    )

    final_risk = np.clip(
        final_risk,
        0,
        100
    )

    final_risk = round(
        float(final_risk),
        2
    )


    # ========================================================
    # RISK LEVEL
    # ========================================================

    if final_risk < 25:

        risk_level = "LOW"

        message = (
            "Low landslide risk under the current "
            "prototype scenario."
        )

    elif final_risk < 50:

        risk_level = "MODERATE"

        message = (
            "Moderate landslide risk. Continue monitoring "
            "vulnerable slopes and weather conditions."
        )

    elif final_risk < 75:

        risk_level = "HIGH"

        message = (
            "High landslide risk. Authorities should "
            "monitor vulnerable slopes and road corridors."
        )

    else:

        risk_level = "CRITICAL"

        message = (
            "Critical landslide risk. Immediate monitoring "
            "and emergency preparedness recommended."
        )


    return {
        "susceptibility": susceptibility,
        "rainfall_trigger": rainfall,
        "soil_moisture_trigger": soil,
        "final_risk": final_risk,
        "risk_level": risk_level,
        "message": message
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = calculate_risk(
        elevation_m=1200,
        slope_deg=35,
        aspect_deg=180,
        rainfall_24h=100,
        rainfall_7d=350,
        soil_moisture=75
    )

    print("=" * 60)
    print("LANDSLIDE RISK ENGINE TEST")
    print("=" * 60)

    print(
        "susceptibility:",
        result["susceptibility"]
    )

    print(
        "rainfall_trigger:",
        result["rainfall_trigger"]
    )

    print(
        "soil_moisture_trigger:",
        result["soil_moisture_trigger"]
    )

    print(
        "final_risk:",
        result["final_risk"]
    )

    print(
        "risk_level:",
        result["risk_level"]
    )

    print(
        "message:",
        result["message"]
    )

    print("=" * 60)