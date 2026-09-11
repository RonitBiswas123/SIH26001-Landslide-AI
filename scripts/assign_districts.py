# ============================================================
# SIH26001
# ASSIGN DISTRICTS TO GSI LANDSLIDE POINTS
# ============================================================

from pathlib import Path
import sys

import pandas as pd
import geopandas as gpd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "processed"

INPUT_FILE = DATA_DIR / "gsi_master_dataset.csv"

OUTPUT_FILE = DATA_DIR / "gsi_master_with_districts.csv"

BOUNDARY_DIR = DATA_DIR / "boundaries"

BOUNDARY_FILE = (
    BOUNDARY_DIR / "india_districts.geojson"
)


BOUNDARY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PUBLIC DISTRICT DATA
# ============================================================

BOUNDARY_URL = (
    "https://raw.githubusercontent.com/"
    "ishawakankar/India_Districts/"
    "master/india_district.geojson"
)


# ============================================================
# DOWNLOAD DISTRICT BOUNDARY
# ============================================================

print("=" * 70)
print("SIH26001 - DISTRICT MAPPING")
print("=" * 70)

print()

print("Checking GSI dataset...")


if not INPUT_FILE.exists():

    print()

    print(
        "ERROR: GSI master dataset not found:"
    )

    print(INPUT_FILE)

    sys.exit(1)


print(
    "GSI dataset found."
)


# ============================================================
# DOWNLOAD BOUNDARIES
# ============================================================

if not BOUNDARY_FILE.exists():

    print()

    print(
        "Downloading India district boundaries..."
    )

    try:

        boundary_gdf = gpd.read_file(
            BOUNDARY_URL
        )

        boundary_gdf.to_file(
            BOUNDARY_FILE,
            driver="GeoJSON"
        )

        print(
            "District boundaries downloaded."
        )

    except Exception as e:

        print()

        print(
            "ERROR downloading district boundaries:"
        )

        print(e)

        sys.exit(1)

else:

    print(
        "District boundary file already exists."
    )


# ============================================================
# LOAD GSI DATA
# ============================================================

print()

print(
    "Loading GSI landslide inventory..."
)


df = pd.read_csv(
    INPUT_FILE
)


print(
    f"GSI records: {len(df):,}"
)


# ============================================================
# CHECK COORDINATES
# ============================================================

required_columns = [
    "latitude",
    "longitude"
]


for column in required_columns:

    if column not in df.columns:

        print(
            f"ERROR: Missing column: {column}"
        )

        sys.exit(1)


df = df.dropna(
    subset=[
        "latitude",
        "longitude"
    ]
).copy()


# ============================================================
# CONVERT TO GEODATAFRAME
# ============================================================

print()

print(
    "Converting GSI points to geographic coordinates..."
)


points = gpd.GeoDataFrame(

    df,

    geometry=gpd.points_from_xy(

        df["longitude"],

        df["latitude"]

    ),

    crs="EPSG:4326"

)


# ============================================================
# LOAD DISTRICT BOUNDARIES
# ============================================================

print()

print(
    "Loading district boundaries..."
)


districts = gpd.read_file(
    BOUNDARY_FILE
)


print(
    f"District polygons: {len(districts):,}"
)


print()

print(
    "Boundary columns:"
)

print(
    list(districts.columns)
)


# ============================================================
# NORMALIZE CRS
# ============================================================

if districts.crs is None:

    districts = districts.set_crs(
        "EPSG:4326"
    )


districts = districts.to_crs(
    "EPSG:4326"
)


# ============================================================
# FIND DISTRICT NAME COLUMN
# ============================================================

possible_name_columns = [

    "district",

    "District",

    "DISTRICT",

    "dtname",

    "DTNAME",

    "shapeName",

    "NAME_2",

    "NAME"

]


district_column = None


for column in possible_name_columns:

    if column in districts.columns:

        district_column = column

        break


if district_column is None:

    print()

    print(
        "ERROR: Could not identify district name column."
    )

    print(
        "Available columns:"
    )

    print(
        list(districts.columns)
    )

    sys.exit(1)


print()

print(
    f"Using district column: {district_column}"
)


# ============================================================
# FIND STATE COLUMN
# ============================================================

possible_state_columns = [

    "state",

    "State",

    "STATE",

    "stname",

    "STNAME",

    "shapeGroup",

    "NAME_1",

    "STATE_NAME"

]


state_column = None


for column in possible_state_columns:

    if column in districts.columns:

        state_column = column

        break


if state_column is None:

    print(
        "Warning: state column not detected."
    )


# ============================================================
# KEEP ONLY REQUIRED COLUMNS
# ============================================================

keep_columns = [
    district_column,
    "geometry"
]


if state_column is not None:

    keep_columns.insert(
        1,
        state_column
    )


districts_small = districts[
    keep_columns
].copy()


# ============================================================
# RENAME COLUMNS
# ============================================================

rename_dict = {

    district_column:
        "district"

}


if state_column is not None:

    rename_dict[
        state_column
    ] = "boundary_state"


districts_small = districts_small.rename(
    columns=rename_dict
)


# ============================================================
# SPATIAL JOIN
# ============================================================

print()

print(
    "Performing point-in-district spatial join..."
)

print(
    "This may take a little while."
)


joined = gpd.sjoin(

    points,

    districts_small,

    how="left",

    predicate="within"

)


# ============================================================
# CLEAN JOIN COLUMNS
# ============================================================

if "index_right" in joined.columns:

    joined = joined.drop(
        columns=["index_right"]
    )


if "geometry" in joined.columns:

    joined = joined.drop(
        columns=["geometry"]
    )


# ============================================================
# DISTRICT COVERAGE
# ============================================================

total_points = len(joined)


matched_points = (

    joined[
        "district"
    ]
    .notna()
    .sum()

)


unmatched_points = (

    total_points -
    matched_points

)


coverage = (

    matched_points /
    total_points *
    100

)


print()

print("=" * 70)

print(
    "DISTRICT MAPPING RESULTS"
)

print("=" * 70)

print()

print(
    f"Total points:       {total_points:,}"
)

print(
    f"Matched districts:  {matched_points:,}"
)

print(
    f"Unmatched points:   {unmatched_points:,}"
)

print(
    f"District coverage:  {coverage:.2f}%"
)


# ============================================================
# STATE / DISTRICT PREVIEW
# ============================================================

print()

print(
    "Sample district assignments:"
)

preview_columns = [

    "latitude",

    "longitude",

    "state",

    "district"

]


available_preview = [

    c

    for c in preview_columns

    if c in joined.columns

]


print(

    joined[
        available_preview
    ].head(15).to_string(
        index=False
    )

)


# ============================================================
# SAVE
# ============================================================

print()

print(
    "Saving district-enriched dataset..."
)


joined.to_csv(

    OUTPUT_FILE,

    index=False
)


print()

print(
    "SUCCESS!"
)

print()

print(
    "Output:"
)

print(
    OUTPUT_FILE
)


# ============================================================
# DISTRICT SUMMARY
# ============================================================

district_summary = (

    joined[
        joined["district"].notna()
    ]

    .groupby(
        "district"
    )

    .size()

    .reset_index(
        name="landslide_points"
    )

    .sort_values(
        "landslide_points",
        ascending=False
    )

)


print()

print(
    "Top 20 districts by historical GSI points:"
)

print()

print(
    district_summary.head(
        20
    ).to_string(
        index=False
    )
)


# ============================================================
# FINISHED
# ============================================================

print()

print("=" * 70)

print(
    "DISTRICT MAPPING COMPLETE"
)

print("=" * 70)