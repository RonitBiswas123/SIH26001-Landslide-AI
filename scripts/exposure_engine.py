import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path


# ============================================================
# LANDSLIDE EXPOSURE ENGINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MASTER_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "master_landslide_dataset.csv"
)

ROADS_FILE = (
    BASE_DIR
    / "data"
    / "exposure"
    / "roads.geojson"
)

SETTLEMENTS_FILE = (
    BASE_DIR
    / "data"
    / "exposure"
    / "settlements.geojson"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

ROAD_RADIUS_KM = 5
SETTLEMENT_RADIUS_KM = 10


# ============================================================
# START
# ============================================================

print("=" * 65)
print("LANDSLIDE EXPOSURE & EMERGENCY PRIORITY ENGINE")
print("=" * 65)


# ============================================================
# LOAD LANDSLIDES
# ============================================================

print("\n[1/5] Loading landslide dataset...")

df = pd.read_csv(
    MASTER_FILE
)

df = df.dropna(
    subset=[
        "latitude",
        "longitude"
    ]
).copy()

print(
    f"Landslide locations: {len(df):,}"
)


# ============================================================
# LOAD ROADS
# ============================================================

print("\n[2/5] Loading roads...")

roads = gpd.read_file(
    ROADS_FILE
)

print(
    f"Road segments: {len(roads):,}"
)


# ============================================================
# LOAD SETTLEMENTS
# ============================================================

print("\n[3/5] Loading settlements...")

settlements = gpd.read_file(
    SETTLEMENTS_FILE
)

print(
    f"Settlements: {len(settlements):,}"
)


# ============================================================
# CREATE LANDSLIDE GEOMETRY
# ============================================================

landslides = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["longitude"],
        df["latitude"]
    ),
    crs="EPSG:4326"
)


# ============================================================
# PROJECT TO METRIC CRS
# ============================================================

print("\nProjecting geographic data...")

landslides = landslides.to_crs(
    "EPSG:3857"
)

roads = roads.to_crs(
    "EPSG:3857"
)

settlements = settlements.to_crs(
    "EPSG:3857"
)


# ============================================================
# BUILD SPATIAL INDEXES
# ============================================================

print("Building spatial indexes...")

road_index = roads.sindex

settlement_index = settlements.sindex


# ============================================================
# DISTANCE FUNCTION
# ============================================================

def nearest_distance(
    point,
    layer,
    index,
    radius
):

    candidates = list(
        index.query(
            point.buffer(radius),
            predicate="intersects"
        )
    )

    if not candidates:
        return np.nan

    geometries = layer.iloc[
        candidates
    ].geometry

    if len(geometries) == 0:
        return np.nan

    distances = geometries.distance(
        point
    )

    return float(
        distances.min()
    )


# ============================================================
# CALCULATE DISTANCES
# ============================================================

print("\n[4/5] Calculating exposure...")

print(
    "This may take a few minutes."
)

road_distances = []
settlement_distances = []

total = len(landslides)

for i, point in enumerate(
    landslides.geometry
):

    road_distance = nearest_distance(
        point,
        roads,
        road_index,
        ROAD_RADIUS_KM * 1000
    )

    settlement_distance = nearest_distance(
        point,
        settlements,
        settlement_index,
        SETTLEMENT_RADIUS_KM * 1000
    )

    road_distances.append(
        road_distance
    )

    settlement_distances.append(
        settlement_distance
    )

    if (i + 1) % 1000 == 0:

        print(
            f"   Processed "
            f"{i + 1:,}/{total:,}"
        )


# ============================================================
# STORE DISTANCES
# ============================================================

landslides[
    "nearest_road_km"
] = (
    np.array(road_distances)
    / 1000
)

landslides[
    "nearest_settlement_km"
] = (
    np.array(settlement_distances)
    / 1000
)


# ============================================================
# ROAD EXPOSURE
# ============================================================

def calculate_road_exposure(
    distance
):

    if pd.isna(distance):
        return 0

    if distance <= 0.25:
        return 100

    elif distance <= 0.5:
        return 90

    elif distance <= 1:
        return 75

    elif distance <= 2:
        return 55

    elif distance <= 5:
        return 30

    return 0


# ============================================================
# SETTLEMENT EXPOSURE
# ============================================================

def calculate_settlement_exposure(
    distance
):

    if pd.isna(distance):
        return 0

    if distance <= 0.5:
        return 100

    elif distance <= 1:
        return 90

    elif distance <= 2:
        return 75

    elif distance <= 5:
        return 50

    elif distance <= 10:
        return 25

    return 0


landslides[
    "road_exposure_score"
] = landslides[
    "nearest_road_km"
].apply(
    calculate_road_exposure
)

landslides[
    "settlement_exposure_score"
] = landslides[
    "nearest_settlement_km"
].apply(
    calculate_settlement_exposure
)


# ============================================================
# COMBINED EXPOSURE
# ============================================================

landslides[
    "exposure_score"
] = (
    0.60
    * landslides[
        "road_exposure_score"
    ]
    +
    0.40
    * landslides[
        "settlement_exposure_score"
    ]
)


# ============================================================
# SUSCEPTIBILITY
# ============================================================

if "susceptibility" in landslides.columns:

    susceptibility = pd.to_numeric(
        landslides[
            "susceptibility"
        ],
        errors="coerce"
    ).fillna(0)

elif "slope_deg" in landslides.columns:

    susceptibility = (
        pd.to_numeric(
            landslides[
                "slope_deg"
            ],
            errors="coerce"
        )
        .fillna(0)
        .clip(0, 60)
        / 60
        * 100
    )

else:

    susceptibility = pd.Series(
        50,
        index=landslides.index
    )


# ============================================================
# EMERGENCY PRIORITY
# ============================================================

landslides[
    "priority_score"
] = (
    0.65
    * susceptibility
    +
    0.35
    * landslides[
        "exposure_score"
    ]
)


landslides[
    "priority_score"
] = (
    landslides[
        "priority_score"
    ]
    .clip(0, 100)
)


# ============================================================
# PRIORITY CLASS
# ============================================================

landslides[
    "priority_level"
] = np.select(
    [
        landslides[
            "priority_score"
        ] >= 75,

        landslides[
            "priority_score"
        ] >= 50,

        landslides[
            "priority_score"
        ] >= 25
    ],
    [
        "IMMEDIATE ACTION",
        "HIGH PRIORITY",
        "MONITOR"
    ],
    default="ROUTINE"
)


# ============================================================
# RETURN TO LAT/LON
# ============================================================

landslides = landslides.to_crs(
    "EPSG:4326"
)


# ============================================================
# SAVE CSV
# ============================================================

print("\n[5/5] Saving results...")

output_csv = (
    OUTPUT_DIR
    / "landslide_exposure_priority.csv"
)

result = pd.DataFrame(
    landslides.drop(
        columns="geometry"
    )
)

result.to_csv(
    output_csv,
    index=False
)


# ============================================================
# SAVE GEOJSON
# ============================================================

output_geojson = (
    OUTPUT_DIR
    / "landslide_exposure_priority.geojson"
)

landslides.to_file(
    output_geojson,
    driver="GeoJSON"
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n")
print("=" * 65)
print("EXPOSURE ENGINE COMPLETE")
print("=" * 65)

print(
    f"\nTotal locations       : "
    f"{len(result):,}"
)

print(
    f"Avg road distance    : "
    f"{result['nearest_road_km'].mean():.2f} km"
)

print(
    f"Avg settlement dist. : "
    f"{result['nearest_settlement_km'].mean():.2f} km"
)

print(
    f"Avg exposure score   : "
    f"{result['exposure_score'].mean():.2f}"
)

print(
    f"Avg priority score   : "
    f"{result['priority_score'].mean():.2f}"
)


print("\nPriority distribution:")

print(
    result[
        "priority_level"
    ]
    .value_counts()
    .to_string()
)


print("\nTop 10 emergency locations:")

top10 = (
    result
    .sort_values(
        "priority_score",
        ascending=False
    )
    .head(10)
)

show_columns = [
    "latitude",
    "longitude",
    "nearest_road_km",
    "nearest_settlement_km",
    "exposure_score",
    "priority_score",
    "priority_level"
]

print(
    top10[
        show_columns
    ].to_string(
        index=False
    )
)


print("\nOutput:")

print(output_csv)
print(output_geojson)

print("=" * 65)