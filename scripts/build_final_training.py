import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

LANDSLIDE_FILE = BASE / "data/processed/master_landslide_dataset.csv"
BACKGROUND_FILE = BASE / "data/processed/terrain_background_samples.csv"
HISTORY_FILE = BASE / "data/processed/district_historical_features.csv"

OUTPUT_FILE = BASE / "data/processed/final_training_dataset.csv"

print("=" * 60)
print("BUILDING FINAL TRAINING DATASET")
print("=" * 60)

# Load files
landslide = pd.read_csv(LANDSLIDE_FILE)
background = pd.read_csv(BACKGROUND_FILE)
history = pd.read_csv(HISTORY_FILE)

# ---------------------------------------------------------
# 1. Keep only landslide points with terrain
# ---------------------------------------------------------

landslide = landslide[
    landslide["elevation_m"].notna() &
    landslide["slope_deg"].notna()
].copy()

print(f"Landslide samples with terrain: {len(landslide)}")
print(f"Background samples:             {len(background)}")

# ---------------------------------------------------------
# 2. Select features for landslide samples
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
# 3. Select background features
# ---------------------------------------------------------

negative = background[
    [
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "aspect_sin",
        "aspect_cos"
    ]
].copy()

negative["district"] = np.nan
negative["label"] = 0

# ---------------------------------------------------------
# 4. Combine
# ---------------------------------------------------------

training = pd.concat(
    [positive, negative],
    ignore_index=True
)

# ---------------------------------------------------------
# 5. Add historical district features ONLY where available
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
# 6. Fill missing historical values
# ---------------------------------------------------------

training["historical_landslide_count"] = (
    training["historical_landslide_count"].fillna(0)
)

training["unique_landslide_locations"] = (
    training["unique_landslide_locations"].fillna(0)
)

# ---------------------------------------------------------
# 7. Remove rows with missing terrain
# ---------------------------------------------------------

training = training.dropna(
    subset=[
        "elevation_m",
        "slope_deg",
        "aspect_deg"
    ]
)

# ---------------------------------------------------------
# 8. Shuffle
# ---------------------------------------------------------

training = training.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# ---------------------------------------------------------
# 9. Save
# ---------------------------------------------------------

training.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------------------------------
# 10. Report
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("FINAL TRAINING DATASET")
print("=" * 60)

print(f"Total samples: {len(training)}")

print("\nClass distribution:")
print(training["label"].value_counts())

print("\nClass percentage:")
print(
    training["label"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

print("\nMissing values:")
print(training.isna().sum())

print("\nFeatures:")
print(list(training.columns))

print("\nSaved:")
print(OUTPUT_FILE)

print("=" * 60)