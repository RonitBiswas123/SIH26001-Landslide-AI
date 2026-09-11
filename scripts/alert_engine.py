import pandas as pd
import numpy as np
from pathlib import Path
import sys

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "processed"

MASTER_FILE = DATA_DIR / "master_landslide_dataset.csv"
EXPOSURE_FILE = DATA_DIR / "landslide_exposure_priority.csv"

OUTPUT_FILE = DATA_DIR / "active_alerts.csv"


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

print("\n==============================================")
print("      LANDSLIDE AUTOMATED ALERT ENGINE")
print("==============================================\n")

print("Loading GSI landslide data...")

df = pd.read_csv(MASTER_FILE)

print(f"GSI locations loaded: {len(df):,}")


# ---------------------------------------------------------
# LOAD EXPOSURE DATA
# ---------------------------------------------------------

print("Loading exposure intelligence...")

try:

    exposure = pd.read_csv(EXPOSURE_FILE)

    exposure_cols = [
        "latitude",
        "longitude",
        "nearest_road_km",
        "nearest_settlement_km",
        "exposure_score",
        "priority_score",
        "priority_level"
    ]

    exposure = exposure[
        [c for c in exposure_cols if c in exposure.columns]
    ]

    exposure = exposure.rename(
        columns={
            "priority_score": "exposure_priority_score",
            "priority_level": "exposure_priority_level"
        }
    )

    # Round coordinates before joining
    df["lat_key"] = df["latitude"].round(5)
    df["lon_key"] = df["longitude"].round(5)

    exposure["lat_key"] = exposure["latitude"].round(5)
    exposure["lon_key"] = exposure["longitude"].round(5)

    df = df.merge(
        exposure.drop(
            columns=["latitude", "longitude"],
            errors="ignore"
        ),
        on=["lat_key", "lon_key"],
        how="left"
    )

except Exception as e:

    print("Exposure data could not be loaded.")
    print("Reason:", e)

    df["nearest_road_km"] = np.nan
    df["nearest_settlement_km"] = np.nan
    df["exposure_score"] = 0
    df["exposure_priority_score"] = 0
    df["exposure_priority_level"] = "ROUTINE"


# ---------------------------------------------------------
# CLEAN
# ---------------------------------------------------------

df["exposure_score"] = pd.to_numeric(
    df["exposure_score"],
    errors="coerce"
).fillna(0)

df["exposure_priority_score"] = pd.to_numeric(
    df["exposure_priority_score"],
    errors="coerce"
).fillna(0)

df["nearest_road_km"] = pd.to_numeric(
    df["nearest_road_km"],
    errors="coerce"
)

df["nearest_settlement_km"] = pd.to_numeric(
    df["nearest_settlement_km"],
    errors="coerce"
)


# ---------------------------------------------------------
# PROTOTYPE WEATHER SCENARIO
# ---------------------------------------------------------
#
# These values represent a warning scenario.
# Replace with IMD values once live weather is connected.
#
# ---------------------------------------------------------

RAINFALL_24H = 150
RAINFALL_7D = 500
SOIL_MOISTURE = 75


# ---------------------------------------------------------
# TERRAIN SUSCEPTIBILITY
# ---------------------------------------------------------

if "slope_deg" in df.columns:

    slope = pd.to_numeric(
        df["slope_deg"],
        errors="coerce"
    ).fillna(0)

    susceptibility = np.clip(
        (slope / 45) * 100,
        0,
        100
    )

else:

    susceptibility = np.zeros(len(df))


# ---------------------------------------------------------
# RAINFALL TRIGGER
# ---------------------------------------------------------

r24 = np.clip(
    RAINFALL_24H / 150,
    0,
    1
)

r7 = np.clip(
    RAINFALL_7D / 500,
    0,
    1
)

rainfall_trigger = (
    0.60 * r24 +
    0.40 * r7
) * 100


# ---------------------------------------------------------
# SOIL MOISTURE TRIGGER
# ---------------------------------------------------------

soil_trigger = np.clip(
    (SOIL_MOISTURE - 40) / 50,
    0,
    1
) * 100


# ---------------------------------------------------------
# DYNAMIC RISK
# ---------------------------------------------------------

df["susceptibility_score"] = susceptibility

df["rainfall_trigger"] = rainfall_trigger

df["soil_moisture_trigger"] = soil_trigger

df["risk_score"] = (
    0.55 * df["susceptibility_score"]
    + 0.30 * df["rainfall_trigger"]
    + 0.15 * df["soil_moisture_trigger"]
)

df["risk_score"] = np.clip(
    df["risk_score"],
    0,
    100
)


# ---------------------------------------------------------
# RISK LEVEL
# ---------------------------------------------------------

df["risk_level"] = np.select(

    [
        df["risk_score"] >= 75,
        df["risk_score"] >= 50,
        df["risk_score"] >= 25
    ],

    [
        "CRITICAL",
        "HIGH",
        "MODERATE"
    ],

    default="LOW"
)


# ---------------------------------------------------------
# COMMAND PRIORITY
# ---------------------------------------------------------

df["command_priority_score"] = (
    0.60 * df["risk_score"]
    + 0.25 * df["exposure_score"]
    + 0.15 * df["exposure_priority_score"]
)

df["command_priority_score"] = np.clip(
    df["command_priority_score"],
    0,
    100
)


# ---------------------------------------------------------
# ALERT LEVEL
# ---------------------------------------------------------

df["alert_level"] = np.select(

    [
        df["command_priority_score"] >= 75,
        df["command_priority_score"] >= 50,
        df["command_priority_score"] >= 25
    ],

    [
        "IMMEDIATE ACTION",
        "HIGH PRIORITY",
        "MONITOR"
    ],

    default="ROUTINE"
)


# ---------------------------------------------------------
# ALERT MESSAGE
# ---------------------------------------------------------

def create_message(row):

    risk = row["risk_score"]
    priority = row["alert_level"]

    road = row["nearest_road_km"]
    settlement = row["nearest_settlement_km"]

    if pd.isna(road):
        road_text = "unknown"
    else:
        road_text = f"{road:.2f} km"

    if pd.isna(settlement):
        settlement_text = "unknown"
    else:
        settlement_text = f"{settlement:.2f} km"

    if priority == "IMMEDIATE ACTION":

        return (
            f"CRITICAL landslide risk detected. "
            f"Risk score {risk:.1f}%. "
            f"Nearest road {road_text}; "
            f"nearest settlement {settlement_text}. "
            f"Immediate field verification and preparedness recommended."
        )

    elif priority == "HIGH PRIORITY":

        return (
            f"High landslide risk detected. "
            f"Risk score {risk:.1f}%. "
            f"Enhanced monitoring and preventive action recommended."
        )

    elif priority == "MONITOR":

        return (
            f"Moderate landslide risk detected. "
            f"Continue monitoring rainfall, terrain and local conditions."
        )

    return (
        f"Low current scenario risk. "
        f"Continue routine monitoring."
    )


df["alert_message"] = df.apply(
    create_message,
    axis=1
)


# ---------------------------------------------------------
# ALERT STATUS
# ---------------------------------------------------------

df["alert_status"] = np.where(
    df["alert_level"].isin(
        ["IMMEDIATE ACTION", "HIGH PRIORITY"]
    ),
    "ACTIVE",
    "MONITORING"
)


# ---------------------------------------------------------
# FINAL ALERT DATASET
# ---------------------------------------------------------

alert_columns = [

    "latitude",
    "longitude",

    "state",
    "district",

    "elevation_m",
    "slope_deg",

    "susceptibility_score",

    "rainfall_trigger",
    "soil_moisture_trigger",

    "risk_score",
    "risk_level",

    "nearest_road_km",
    "nearest_settlement_km",

    "exposure_score",

    "command_priority_score",
    "alert_level",

    "alert_status",
    "alert_message"
]

alert_columns = [
    c for c in alert_columns
    if c in df.columns
]

alerts = df[alert_columns].copy()


# ---------------------------------------------------------
# SORT BY PRIORITY
# ---------------------------------------------------------

alerts = alerts.sort_values(
    "command_priority_score",
    ascending=False
)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

alerts.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

print("\n==============================================")
print("             ALERT SUMMARY")
print("==============================================")

print(
    "\nCRITICAL:",
    (alerts["risk_level"] == "CRITICAL").sum()
)

print(
    "HIGH:",
    (alerts["risk_level"] == "HIGH").sum()
)

print(
    "MODERATE:",
    (alerts["risk_level"] == "MODERATE").sum()
)

print(
    "LOW:",
    (alerts["risk_level"] == "LOW").sum()
)

print("\nCommand Priority:")

print(
    alerts["alert_level"]
    .value_counts()
)


print("\nTOP 10 ALERTS")

print(
    alerts[
        [
            "latitude",
            "longitude",
            "risk_score",
            "risk_level",
            "exposure_score",
            "command_priority_score",
            "alert_level"
        ]
    ].head(10).to_string(index=False)
)


print("\n==============================================")
print("ALERT ENGINE COMPLETE")
print("==============================================")

print("\nSaved:")print(OUTPUT_FILE)