import pandas as pd
from pathlib import Path

INPUT_FILE = "data/processed/gsi_district_mapped.csv"
OUTPUT_FILE = "data/processed/district_historical_features.csv"

print("=" * 60)
print("BUILDING HISTORICAL LANDSLIDE FEATURES")
print("=" * 60)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("\nTotal GSI records:", len(df))

# Only records with a district
df_valid = df.dropna(subset=["district"]).copy()

print("Records with district:", len(df_valid))

# --------------------------------------------------
# FEATURE 1: TOTAL HISTORICAL LANDSLIDES
# --------------------------------------------------

features = (
    df_valid
    .groupby("district")
    .size()
    .reset_index(name="historical_landslide_count")
)

# --------------------------------------------------
# FEATURE 2: UNIQUE LOCATIONS
# --------------------------------------------------

unique_locations = (
    df_valid
    .groupby("district")
    .apply(
        lambda x: x[
            ["latitude", "longitude"]
        ].drop_duplicates().shape[0],
        include_groups=False
    )
    .reset_index(name="unique_landslide_locations")
)

features = features.merge(
    unique_locations,
    on="district",
    how="left"
)

# --------------------------------------------------
# FEATURE 3: FIRST / LAST YEAR
# --------------------------------------------------

if "year" in df_valid.columns:

    df_valid["year"] = pd.to_numeric(
        df_valid["year"],
        errors="coerce"
    )

    year_features = (
        df_valid
        .groupby("district")["year"]
        .agg(
            first_recorded_year="min",
            latest_recorded_year="max"
        )
        .reset_index()
    )

    features = features.merge(
        year_features,
        on="district",
        how="left"
    )

# --------------------------------------------------
# FEATURE 4: LANDSLIDES PER YEAR
# --------------------------------------------------

features["observation_years"] = (
    features["latest_recorded_year"]
    - features["first_recorded_year"]
    + 1
)

features["landslides_per_year"] = (
    features["historical_landslide_count"]
    /
    features["observation_years"]
)

# --------------------------------------------------
# SORT
# --------------------------------------------------

features = features.sort_values(
    "historical_landslide_count",
    ascending=False
)

# --------------------------------------------------
# SAVE
# --------------------------------------------------

Path("data/processed").mkdir(
    parents=True,
    exist_ok=True
)

features.to_csv(
    OUTPUT_FILE,
    index=False
)

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------

print("\n" + "=" * 60)
print("HISTORICAL FEATURES COMPLETE")
print("=" * 60)

print("Districts:", len(features))

print("\nTop 20 districts:")

print(
    features.head(20).to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)