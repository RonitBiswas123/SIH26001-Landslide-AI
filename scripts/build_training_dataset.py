import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neighbors import BallTree

BASE = Path(__file__).resolve().parents[1]

LANDSLIDE_FILE = BASE / "data/processed/master_landslide_dataset.csv"
BACKGROUND_FILE = BASE / "data/processed/background_samples.csv"
TERRAIN_FILE = BASE / "data/processed/terrain_features.csv"
HISTORY_FILE = BASE / "data/processed/district_historical_features.csv"

OUTPUT_FILE = BASE / "data/processed/training_dataset.csv"

print("=" * 60)
print("BUILDING ML TRAINING DATASET")
print("=" * 60)

# ---------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------

landslide = pd.read_csv(LANDSLIDE_FILE)
background = pd.read_csv(BACKGROUND_FILE)
terrain = pd.read_csv(TERRAIN_FILE)
history = pd.read_csv(HISTORY_FILE)

print(f"Landslide samples:  {len(landslide)}")
print(f"Background samples: {len(background)}")
print(f"Terrain records:    {len(terrain)}")
print(f"History districts:  {len(history)}")

# ---------------------------------------------------------
# 2. Prepare positive samples
# ---------------------------------------------------------

positive = landslide[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "aspect_sin",
        "aspect_cos",
        "district"
    ]
].copy()

positive["label"] = 1

# ---------------------------------------------------------
# 3. Remove duplicate terrain coordinates
# ---------------------------------------------------------

terrain = terrain[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg"
    ]
].drop_duplicates(
    subset=["latitude", "longitude"]
)

# ---------------------------------------------------------
# 4. Attach terrain to background points
# ---------------------------------------------------------

background = background.merge(
    terrain,
    on=["latitude", "longitude"],
    how="left"
)

# ---------------------------------------------------------
# 5. Find district for background points
# ---------------------------------------------------------

# Use nearest known landslide district as a practical
# prototype approximation.

landslide_coords = np.radians(
    landslide[
        ["latitude", "longitude"]
    ].dropna().values
)

landslide_districts = landslide[
    ["latitude", "longitude", "district"]
].dropna()

tree = BallTree(
    np.radians(
        landslide_districts[
            ["latitude", "longitude"]
        ].values
    ),
    metric="haversine"
)

background_coords = np.radians(
    background[
        ["latitude", "longitude"]
    ].values
)

_, nearest_idx = tree.query(
    background_coords,
    k=1
)

background["district"] = (
    landslide_districts.iloc[
        nearest_idx[:, 0]
    ]["district"].values
)

background["label"] = 0

# ---------------------------------------------------------
# 6. Select same columns
# ---------------------------------------------------------

positive = positive[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "aspect_sin",
        "aspect_cos",
        "district",
        "label"
    ]
]

background = background[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "district",
        "label"
    ]
]

# Recreate aspect features for background
background["aspect_sin"] = np.sin(
    np.radians(background["aspect_deg"])
)

background["aspect_cos"] = np.cos(
    np.radians(background["aspect_deg"])
)

# Reorder columns
background = background[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "aspect_sin",
        "aspect_cos",
        "district",
        "label"
    ]
]

# ---------------------------------------------------------
# 7. Combine positive + negative
# ---------------------------------------------------------

training = pd.concat(
    [positive, background],
    ignore_index=True
)

# ---------------------------------------------------------
# 8. Add historical district features
# ---------------------------------------------------------

history_small = history[
    [
        "district",
        "historical_landslide_count",
        "unique_landslide_locations"
    ]
].drop_duplicates(
    subset=["district"]
)

training = training.merge(
    history_small,
    on="district",
    how="left"
)

# ---------------------------------------------------------
# 9. Clean infinite values
# ---------------------------------------------------------

training.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

# ---------------------------------------------------------
# 10. Save
# ---------------------------------------------------------

training.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------------------------------
# 11. Report
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("TRAINING DATASET CREATED")
print("=" * 60)

print(f"Total samples: {len(training)}")

print("\nClass distribution:")
print(training["label"].value_counts())

print("\nMissing values:")
print(training.isna().sum())

print("\nFeatures:")
print(list(training.columns))

print("\nSaved:")
print(OUTPUT_FILE)

print("=" * 60)