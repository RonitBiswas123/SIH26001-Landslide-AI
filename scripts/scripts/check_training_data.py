import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

FILE = BASE / "data/processed/training_dataset.csv"

df = pd.read_csv(FILE)

print("=" * 60)
print("TRAINING DATA QUALITY CHECK")
print("=" * 60)

print(f"Total rows: {len(df)}")

# Rows with terrain
terrain_ok = df[
    df["elevation_m"].notna() &
    df["slope_deg"].notna()
]

print(f"\nRows with terrain: {len(terrain_ok)}")

print("\nClass distribution WITH terrain:")

print(
    terrain_ok["label"].value_counts()
)

print("\nClass percentages:")

print(
    terrain_ok["label"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

print("\nTerrain statistics:")

print(
    terrain_ok[
        [
            "elevation_m",
            "slope_deg",
            "aspect_deg"
        ]
    ].describe()
)

print("\nDistrict missing:")

print(
    terrain_ok["district"].isna().sum()
)

print("=" * 60)