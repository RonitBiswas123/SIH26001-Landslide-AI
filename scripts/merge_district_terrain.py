import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DISTRICT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "gsi_master_with_districts.csv"
)

TERRAIN_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "master_landslide_dataset.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "master_landslide_dataset_with_districts.csv"
)

print("=" * 70)
print("MERGING DISTRICT + TERRAIN DATA")
print("=" * 70)

print("\nLoading district dataset...")
district_df = pd.read_csv(DISTRICT_FILE)

print("District dataset shape:", district_df.shape)
print("District columns:")
print(district_df.columns.tolist())

print("\nLoading terrain dataset...")
terrain_df = pd.read_csv(TERRAIN_FILE)

print("Terrain dataset shape:", terrain_df.shape)
print("Terrain columns:")
print(terrain_df.columns.tolist())

# ---------------------------------------------------------
# Required columns
# ---------------------------------------------------------

terrain_required = [
    "latitude",
    "longitude",
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos"
]

district_required = [
    "latitude",
    "longitude"
]

for col in terrain_required:
    if col not in terrain_df.columns:
        raise ValueError(
            f"Terrain dataset is missing required column: {col}"
        )

for col in district_required:
    if col not in district_df.columns:
        raise ValueError(
            f"District dataset is missing required column: {col}"
        )

# ---------------------------------------------------------
# Keep only useful district information
# ---------------------------------------------------------

district_columns = [
    "latitude",
    "longitude"
]

# Add district/state columns if available
for col in [
    "district",
    "state",
    "state_name",
    "district_name"
]:
    if col in district_df.columns:
        district_columns.append(col)

district_small = district_df[district_columns].copy()

# ---------------------------------------------------------
# Remove duplicate coordinates from district data
# ---------------------------------------------------------

district_small = district_small.drop_duplicates(
    subset=["latitude", "longitude"]
)

print("\nUnique district coordinates:", len(district_small))

# ---------------------------------------------------------
# Merge
# ---------------------------------------------------------

print("\nMerging datasets on latitude + longitude...")

merged = terrain_df.merge(
    district_small,
    on=["latitude", "longitude"],
    how="left",
    suffixes=("", "_district")
)

# ---------------------------------------------------------
# Handle duplicate state/district columns
# ---------------------------------------------------------

for col in ["district", "state", "state_name", "district_name"]:
    district_col = col + "_district"

    if district_col in merged.columns:

        if col in merged.columns:
            merged[col] = merged[col].fillna(
                merged[district_col]
            )
            merged.drop(columns=[district_col], inplace=True)

        else:
            merged.rename(
                columns={district_col: col},
                inplace=True
            )

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

merged.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("MERGE COMPLETE")
print("=" * 70)

print("Output:", OUTPUT_FILE)
print("Rows:", len(merged))
print("Columns:", len(merged.columns))

print("\nFinal columns:")
print(merged.columns.tolist())

print("\nTerrain coverage:")

for col in [
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos"
]:
    valid = merged[col].notna().sum()
    print(
        f"{col}: {valid}/{len(merged)} "
        f"({valid / len(merged) * 100:.2f}%)"
    )

if "district" in merged.columns:
    print(
        "\nDistrict coverage:",
        merged["district"].notna().sum(),
        "/",
        len(merged)
    )

if "state" in merged.columns:
    print(
        "State coverage:",
        merged["state"].notna().sum(),
        "/",
        len(merged)
    )

print("\nSaved successfully.")