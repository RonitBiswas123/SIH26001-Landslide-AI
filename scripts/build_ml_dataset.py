import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

gsi_file = BASE / "data/processed/gsi_district_mapped.csv"
terrain_file = BASE / "data/processed/terrain_features.csv"
history_file = BASE / "data/processed/district_historical_features.csv"

output_file = BASE / "data/processed/master_landslide_dataset.csv"

print("=" * 60)
print("BUILDING MASTER ML DATASET")
print("=" * 60)

# Load data
gsi = pd.read_csv(gsi_file)
terrain = pd.read_csv(terrain_file)
history = pd.read_csv(history_file)

print(f"GSI records:       {len(gsi)}")
print(f"Terrain records:   {len(terrain)}")
print(f"History districts: {len(history)}")

# ---------------------------------------------------------
# 1. Remove duplicate coordinates from terrain
# ---------------------------------------------------------

terrain_cols = [
    "latitude",
    "longitude",
    "elevation_m",
    "slope_deg",
    "aspect_deg"
]

terrain_small = terrain[terrain_cols].copy()

terrain_small = terrain_small.drop_duplicates(
    subset=["latitude", "longitude"]
)

print(f"Unique terrain locations: {len(terrain_small)}")

# ---------------------------------------------------------
# 2. Merge terrain
# ---------------------------------------------------------

master = gsi.merge(
    terrain_small,
    on=["latitude", "longitude"],
    how="left"
)

print(f"After terrain merge: {len(master)}")

# ---------------------------------------------------------
# 3. Merge historical features
# ---------------------------------------------------------

history_cols = [
    "district",
    "historical_landslide_count",
    "unique_landslide_locations"
]

history_small = history[history_cols].copy()

history_small = history_small.drop_duplicates(
    subset=["district"]
)

master = master.merge(
    history_small,
    on="district",
    how="left"
)

print(f"After history merge: {len(master)}")

# ---------------------------------------------------------
# 4. Aspect cyclic features
# ---------------------------------------------------------

master["aspect_sin"] = np.sin(
    np.radians(master["aspect_deg"])
)

master["aspect_cos"] = np.cos(
    np.radians(master["aspect_deg"])
)

# ---------------------------------------------------------
# 5. Clean infinite values
# ---------------------------------------------------------

master.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

# ---------------------------------------------------------
# 6. Save
# ---------------------------------------------------------

master.to_csv(
    output_file,
    index=False
)

# ---------------------------------------------------------
# 7. Report
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("MASTER DATASET CREATED")
print("=" * 60)

print(f"Rows: {len(master)}")
print(f"Columns: {len(master.columns)}")

print("\nMissing values:")

print(
    master[
        [
            "elevation_m",
            "slope_deg",
            "aspect_deg",
            "historical_landslide_count",
            "unique_landslide_locations"
        ]
    ].isna().sum()
)

print("\nColumns:")
print(list(master.columns))

print("\nSaved:")
print(output_file)

print("=" * 60)