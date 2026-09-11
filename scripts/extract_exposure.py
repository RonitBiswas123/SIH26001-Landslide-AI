import geopandas as gpd
import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PBF = BASE_DIR / "data" / "exposure" / "ner.osm.pbf"
OUT = BASE_DIR / "data" / "exposure"

OUT.mkdir(parents=True, exist_ok=True)


print("=" * 65)
print("NER EXPOSURE DATA EXTRACTION")
print("=" * 65)

print(f"\nInput: {PBF}\n")


# ============================================================
# 1. ROADS
# ============================================================

print("1/3 Reading roads...")

roads = gpd.read_file(
    PBF,
    layer="lines",
    engine="pyogrio"
)

print(f"   Total line features: {len(roads):,}")


# OSM highway categories we care about
road_types = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "service",
    "living_street"
}


if "highway" in roads.columns:

    roads = roads[
        roads["highway"].isin(road_types)
    ].copy()

else:

    print("   WARNING: highway field not found.")


# Keep useful columns
keep = [
    c for c in [
        "osm_id",
        "name",
        "highway",
        "ref",
        "geometry"
    ]
    if c in roads.columns
]

roads = roads[keep]

roads = roads[
    roads.geometry.notna()
].copy()


roads = roads.to_crs("EPSG:4326")


roads_file = OUT / "roads.geojson"

roads.to_file(
    roads_file,
    driver="GeoJSON",
    engine="pyogrio"
)

print(f"   Roads extracted: {len(roads):,}")
print(f"   Saved: {roads_file}")


# ============================================================
# 2. SETTLEMENTS
# ============================================================

print("\n2/3 Reading settlements...")

points = gpd.read_file(
    PBF,
    layer="points",
    engine="pyogrio"
)

print(f"   Total point features: {len(points):,}")


settlement_types = {
    "city",
    "town",
    "village",
    "hamlet",
    "suburb"
}


if "place" in points.columns:

    settlements = points[
        points["place"].isin(
            settlement_types
        )
    ].copy()

else:

    settlements = points.iloc[0:0].copy()
    print("   WARNING: place field not found.")


keep = [
    c for c in [
        "osm_id",
        "name",
        "place",
        "population",
        "geometry"
    ]
    if c in settlements.columns
]

settlements = settlements[keep]

settlements = settlements[
    settlements.geometry.notna()
].copy()

settlements = settlements.to_crs("EPSG:4326")


settlements_file = OUT / "settlements.geojson"

settlements.to_file(
    settlements_file,
    driver="GeoJSON",
    engine="pyogrio"
)

print(
    f"   Settlements extracted: "
    f"{len(settlements):,}"
)

print(f"   Saved: {settlements_file}")


# ============================================================
# 3. INFRASTRUCTURE
# ============================================================

print("\n3/3 Reading infrastructure...")

infrastructure = points.copy()


# ------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------

health_types = {
    "hospital",
    "clinic",
    "doctors",
    "health_centre"
}


health = infrastructure[
    infrastructure.get(
        "amenity",
        pd.Series(
            index=infrastructure.index,
            dtype="object"
        )
    ).isin(health_types)
].copy()


if len(health) > 0:

    health["asset_type"] = "health"


# ------------------------------------------------------------
# EDUCATION
# ------------------------------------------------------------

education_types = {
    "school",
    "college",
    "university",
    "kindergarten"
}


education = infrastructure[
    infrastructure.get(
        "amenity",
        pd.Series(
            index=infrastructure.index,
            dtype="object"
        )
    ).isin(education_types)
].copy()


if len(education) > 0:

    education["asset_type"] = "education"


# ------------------------------------------------------------
# COMBINE
# ------------------------------------------------------------

infra_parts = []

if len(health) > 0:
    infra_parts.append(health)

if len(education) > 0:
    infra_parts.append(education)


if infra_parts:

    infra = gpd.GeoDataFrame(
        pd.concat(
            infra_parts,
            ignore_index=True
        ),
        crs=points.crs
    )

else:

    infra = points.iloc[0:0].copy()
    infra["asset_type"] = None


# ------------------------------------------------------------
# KEEP COLUMNS
# ------------------------------------------------------------

keep = [
    c for c in [
        "osm_id",
        "name",
        "amenity",
        "asset_type",
        "geometry"
    ]
    if c in infra.columns
]

infra = infra[keep]

infra = infra[
    infra.geometry.notna()
].copy()

infra = infra.to_crs("EPSG:4326")


infra_file = OUT / "infrastructure.geojson"

infra.to_file(
    infra_file,
    driver="GeoJSON",
    engine="pyogrio"
)


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 65)
print("EXTRACTION COMPLETE")
print("=" * 65)

print(
    f"\nRoad segments       : {len(roads):,}"
)

print(
    f"Settlements         : {len(settlements):,}"
)

print(
    f"Infrastructure      : {len(infra):,}"
)


if len(infra) > 0 and "asset_type" in infra.columns:

    print("\nInfrastructure breakdown:")

    print(
        infra["asset_type"]
        .value_counts()
        .to_string()
    )


print("\nOutput files:")

print(f"  {roads_file}")
print(f"  {settlements_file}")
print(f"  {infra_file}")

print("\nDone.")
print("=" * 65)