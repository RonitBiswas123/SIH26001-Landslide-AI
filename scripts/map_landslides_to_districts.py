import pandas as pd
import geopandas as gpd
from pathlib import Path

GSI_FILE = "data/processed/gsi_master_dataset.csv"
BOUNDARY_FILE = "data/raw/boundaries/india_districts.geojson"
OUTPUT_FILE = "data/processed/gsi_district_mapped.csv"

print("=" * 60)
print("GSI LANDSLIDE → DISTRICT MAPPING")
print("=" * 60)

# --------------------------------------------------
# 1. LOAD GSI DATA
# --------------------------------------------------

print("\n[1/5] Loading GSI inventory...")

df = pd.read_csv(GSI_FILE)

print("GSI records:", len(df))

# Keep only records having coordinates
df = df.dropna(
    subset=["latitude", "longitude"]
).copy()

print("Records with coordinates:", len(df))

# --------------------------------------------------
# 2. CONVERT TO GEOSPATIAL POINTS
# --------------------------------------------------

print("\n[2/5] Creating geographic points...")

points = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["longitude"],
        df["latitude"]
    ),
    crs="EPSG:4326"
)

# --------------------------------------------------
# 3. LOAD DISTRICT BOUNDARIES
# --------------------------------------------------

print("\n[3/5] Loading district boundaries...")

districts = gpd.read_file(
    BOUNDARY_FILE
)

print("District polygons:", len(districts))

# Ensure same coordinate system
districts = districts.to_crs("EPSG:4326")

# Keep only required columns
districts = districts[
    ["shapeName", "geometry"]
].copy()

districts = districts.rename(
    columns={
        "shapeName": "district"
    }
)

# --------------------------------------------------
# 4. SPATIAL JOIN
# --------------------------------------------------

print("\n[4/5] Mapping landslides to districts...")
print("This may take a little while...")

mapped = gpd.sjoin(
    points,
    districts,
    how="left",
    predicate="within"
)

# Remove unnecessary GeoPandas column
if "index_right" in mapped.columns:
    mapped = mapped.drop(
        columns=["index_right"]
    )

# Remove geometry before saving CSV
mapped = pd.DataFrame(mapped.drop(
    columns=["geometry"]
))

# --------------------------------------------------
# 5. SAVE
# --------------------------------------------------

print("\n[5/5] Saving dataset...")

Path(
    "data/processed"
).mkdir(
    parents=True,
    exist_ok=True
)

mapped.to_csv(
    OUTPUT_FILE,
    index=False
)

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

matched = mapped["district"].notna().sum()
unmatched = mapped["district"].isna().sum()

print("\n" + "=" * 60)
print("MAPPING COMPLETE")
print("=" * 60)

print("Total records :", len(mapped))
print("Matched       :", matched)
print("Unmatched     :", unmatched)

match_percentage = (
    matched / len(mapped)
) * 100

print(
    f"Match rate    : {match_percentage:.2f}%"
)

print("\nTop 20 districts:")

print(
    mapped["district"]
    .value_counts()
    .head(20)
)

print("\nOutput:")
print(OUTPUT_FILE)