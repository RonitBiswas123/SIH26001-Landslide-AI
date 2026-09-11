import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neighbors import BallTree

BASE = Path(__file__).resolve().parents[1]

LANDSLIDE_FILE = BASE / "data/processed/master_landslide_dataset.csv"
TERRAIN_FILE = BASE / "data/processed/terrain_features.csv"
OUTPUT_FILE = BASE / "data/processed/terrain_background_samples.csv"

RANDOM_SEED = 42
MIN_DISTANCE_KM = 5.0

print("=" * 60)
print("CREATING TERRAIN-MATCHED BACKGROUND SAMPLES")
print("=" * 60)

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

landslide = pd.read_csv(LANDSLIDE_FILE)

terrain = pd.read_csv(TERRAIN_FILE)

# Only terrain locations where slope/elevation exists
terrain = terrain[
    terrain["elevation_m"].notna() &
    terrain["slope_deg"].notna()
].copy()

terrain = terrain.drop_duplicates(
    subset=["latitude", "longitude"]
)

print(f"Terrain-covered locations: {len(terrain)}")

# ---------------------------------------------------------
# Identify terrain-covered geographic region
# ---------------------------------------------------------

lat_min = terrain["latitude"].min()
lat_max = terrain["latitude"].max()

lon_min = terrain["longitude"].min()
lon_max = terrain["longitude"].max()

print("\nTerrain bounds:")
print(f"Latitude:  {lat_min:.4f} -> {lat_max:.4f}")
print(f"Longitude: {lon_min:.4f} -> {lon_max:.4f}")

# ---------------------------------------------------------
# Known landslide locations
# ---------------------------------------------------------

landslide_points = landslide[
    ["latitude", "longitude"]
].dropna().drop_duplicates()

tree = BallTree(
    np.radians(
        landslide_points[
            ["latitude", "longitude"]
        ].values
    ),
    metric="haversine"
)

# ---------------------------------------------------------
# Generate candidates ONLY inside terrain coverage
# ---------------------------------------------------------

rng = np.random.default_rng(RANDOM_SEED)

target = len(terrain)

accepted = []

print(f"\nTarget background samples: {target}")
print("Generating...")

while len(accepted) < target:

    # Generate candidate coordinates
    candidate_lat = rng.uniform(
        lat_min,
        lat_max,
        10000
    )

    candidate_lon = rng.uniform(
        lon_min,
        lon_max,
        10000
    )

    candidates = np.column_stack(
        [candidate_lat, candidate_lon]
    )

    # Find nearest GSI landslide
    distances, _ = tree.query(
        np.radians(candidates),
        k=1
    )

    distances_km = (
        distances[:, 0] * 6371.0
    )

    # Keep candidates at least 5 km away
    valid = distances_km >= MIN_DISTANCE_KM

    valid_candidates = candidates[valid]

    for lat, lon in valid_candidates:

        accepted.append(
            {
                "latitude": lat,
                "longitude": lon,
                "label": 0
            }
        )

        if len(accepted) >= target:
            break

    if len(accepted) % 1000 < 10000:
        print(
            f"Generated: {len(accepted)}/{target}"
        )

# ---------------------------------------------------------
# Convert to dataframe
# ---------------------------------------------------------

background = pd.DataFrame(accepted)

background = background.drop_duplicates(
    subset=["latitude", "longitude"]
)

# ---------------------------------------------------------
# Attach terrain using nearest terrain location
# ---------------------------------------------------------

terrain_tree = BallTree(
    np.radians(
        terrain[
            ["latitude", "longitude"]
        ].values
    ),
    metric="haversine"
)

distances, indices = terrain_tree.query(
    np.radians(
        background[
            ["latitude", "longitude"]
        ].values
    ),
    k=1
)

nearest = terrain.iloc[
    indices[:, 0]
].reset_index(drop=True)

background["elevation_m"] = (
    nearest["elevation_m"].values
)

background["slope_deg"] = (
    nearest["slope_deg"].values
)

background["aspect_deg"] = (
    nearest["aspect_deg"].values
)

background["aspect_sin"] = np.sin(
    np.radians(background["aspect_deg"])
)

background["aspect_cos"] = np.cos(
    np.radians(background["aspect_deg"])
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

background.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 60)
print("TERRAIN-MATCHED BACKGROUND COMPLETE")
print("=" * 60)

print(f"Background samples: {len(background)}")
print(f"Terrain missing: {background['slope_deg'].isna().sum()}")

print("\nExample:")
print(background.head())

print("\nSaved:")
print(OUTPUT_FILE)

print("=" * 60)