import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neighbors import BallTree

BASE = Path(__file__).resolve().parents[1]

INPUT = BASE / "data/processed/master_landslide_dataset.csv"
OUTPUT = BASE / "data/processed/background_samples.csv"

RANDOM_SEED = 42
NEGATIVE_RATIO = 1.0

# Minimum distance from a known landslide
# Background points closer than this are rejected.
MIN_DISTANCE_KM = 5.0

print("=" * 60)
print("CREATING BACKGROUND / NON-LANDSLIDE SAMPLES")
print("=" * 60)

# ---------------------------------------------------------
# 1. Load GSI landslide points
# ---------------------------------------------------------

df = pd.read_csv(INPUT)

points = df[
    ["latitude", "longitude"]
].dropna().drop_duplicates()

print(f"Unique landslide locations: {len(points)}")

# ---------------------------------------------------------
# 2. Set number of background samples
# ---------------------------------------------------------

target_count = int(
    len(points) * NEGATIVE_RATIO
)

print(f"Target background samples: {target_count}")
print(f"Minimum distance: {MIN_DISTANCE_KM} km")

# ---------------------------------------------------------
# 3. Geographic bounding box
# ---------------------------------------------------------

lat_min = points["latitude"].min()
lat_max = points["latitude"].max()

lon_min = points["longitude"].min()
lon_max = points["longitude"].max()

print("\nGeographic bounds:")
print(f"Latitude:  {lat_min:.4f} → {lat_max:.4f}")
print(f"Longitude: {lon_min:.4f} → {lon_max:.4f}")

# ---------------------------------------------------------
# 4. BallTree for fast distance checking
# ---------------------------------------------------------

earth_radius_km = 6371.0

landslide_coords = np.radians(
    points[["latitude", "longitude"]].values
)

tree = BallTree(
    landslide_coords,
    metric="haversine"
)

# ---------------------------------------------------------
# 5. Generate random candidate points
# ---------------------------------------------------------

rng = np.random.default_rng(RANDOM_SEED)

accepted = []

batch_size = 10000

print("\nGenerating background points...")

while len(accepted) < target_count:

    candidate_lat = rng.uniform(
        lat_min,
        lat_max,
        batch_size
    )

    candidate_lon = rng.uniform(
        lon_min,
        lon_max,
        batch_size
    )

    candidates = np.column_stack(
        [candidate_lat, candidate_lon]
    )

    candidate_rad = np.radians(candidates)

    # Find nearest known landslide
    distances, _ = tree.query(
        candidate_rad,
        k=1
    )

    distances_km = (
        distances[:, 0] * earth_radius_km
    )

    # Keep only sufficiently distant points
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

        if len(accepted) >= target_count:
            break

    if len(accepted) % 1000 < batch_size:
        print(
            f"Generated: {len(accepted)}/{target_count}"
        )

# ---------------------------------------------------------
# 6. Create dataframe
# ---------------------------------------------------------

background = pd.DataFrame(accepted)

background = background.drop_duplicates(
    subset=["latitude", "longitude"]
)

# Keep exact requested number
background = background.head(target_count)

# ---------------------------------------------------------
# 7. Save
# ---------------------------------------------------------

background.to_csv(
    OUTPUT,
    index=False
)

print("\n" + "=" * 60)
print("BACKGROUND SAMPLE CREATION COMPLETE")
print("=" * 60)

print(f"Background samples: {len(background)}")
print(f"Label: 0")
print(f"Minimum distance: {MIN_DISTANCE_KM} km")

print("\nExample:")
print(background.head())

print("\nSaved:")
print(OUTPUT)

print("=" * 60)