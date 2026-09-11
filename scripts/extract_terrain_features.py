import os
import math
import numpy as np
import pandas as pd
import rasterio


INPUT_FILE = "data/processed/gsi_district_mapped.csv"
DEM_DIR = "data/raw/dem"
OUTPUT_FILE = "data/processed/terrain_features.csv"


print("=" * 60)
print("EXTRACTING TERRAIN FEATURES")
print("=" * 60)


# ------------------------------------------------------------
# LOAD GSI DATA
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("GSI records:", len(df))


# ------------------------------------------------------------
# CACHE OPEN DEM FILES
# ------------------------------------------------------------

dem_cache = {}

for filename in os.listdir(DEM_DIR):

    if not filename.endswith(".tif"):
        continue

    path = os.path.join(DEM_DIR, filename)

    try:
        src = rasterio.open(path)
        dem_cache[filename[:-4]] = src
    except Exception as e:
        print("Could not open:", filename, e)


print("DEM tiles available:", len(dem_cache))


# ------------------------------------------------------------
# TERRAIN CALCULATION
# ------------------------------------------------------------

def get_features(src, lat, lon):

    try:

        # Convert geographic coordinate to raster pixel
        row, col = src.index(lon, lat)

        # Make sure point is inside raster
        if (
            row < 0
            or col < 0
            or row >= src.height
            or col >= src.width
        ):
            return np.nan, np.nan, np.nan

        # 3x3 neighborhood
        r0 = max(0, row - 1)
        r1 = min(src.height, row + 2)

        c0 = max(0, col - 1)
        c1 = min(src.width, col + 2)

        window = rasterio.windows.Window(
            c0,
            r0,
            c1 - c0,
            r1 - r0
        )

        elevation = src.read(1, window=window).astype(float)

        nodata = src.nodata

        if nodata is not None:
            elevation[elevation == nodata] = np.nan

        if np.all(np.isnan(elevation)):
            return np.nan, np.nan, np.nan

        # Center pixel
        cr = row - r0
        cc = col - c0

        elev = elevation[cr, cc]

        if np.isnan(elev):
            elev = np.nanmedian(elevation)

        # Need neighborhood for slope/aspect
        if elevation.shape[0] < 3 or elevation.shape[1] < 3:
            return elev, np.nan, np.nan

        # Fill tiny missing areas using median
        if np.isnan(elevation).any():
            median = np.nanmedian(elevation)
            elevation[np.isnan(elevation)] = median

        transform = src.window_transform(window)

        # Pixel dimensions in degrees
        dx = abs(transform.a)
        dy = abs(transform.e)

        # Convert approximate degree distance to metres
        lat_factor = 111320
        lon_factor = 111320 * math.cos(
            math.radians(lat)
        )

        dx_m = dx * lon_factor
        dy_m = dy * lat_factor

        # Gradient
        gy, gx = np.gradient(
            elevation,
            dy_m,
            dx_m
        )

        # Slope
        slope = np.degrees(
            np.arctan(
                np.sqrt(gx ** 2 + gy ** 2)
            )
        )

        # Aspect
        aspect = np.degrees(
            np.arctan2(-gx, gy)
        )

        aspect = (aspect + 360) % 360

        return (
            float(elev),
            float(slope[cr, cc]),
            float(aspect[cr, cc])
        )

    except Exception:
        return np.nan, np.nan, np.nan


# ------------------------------------------------------------
# PROCESS RECORDS
# ------------------------------------------------------------

results = []

total = len(df)

for i, row in df.iterrows():

    lat = float(row["latitude"])
    lon = float(row["longitude"])

    lat_floor = math.floor(lat)
    lon_floor = math.floor(lon)

    ns = "N" if lat_floor >= 0 else "S"
    ew = "E" if lon_floor >= 0 else "W"

    tile = (
        f"{ns}{abs(lat_floor):02d}"
        f"{ew}{abs(lon_floor):03d}"
    )

    src = dem_cache.get(tile)

    if src is None:

        elev = np.nan
        slope = np.nan
        aspect = np.nan

    else:

        elev, slope, aspect = get_features(
            src,
            lat,
            lon
        )

    results.append({
        "latitude": lat,
        "longitude": lon,
        "elevation_m": elev,
        "slope_deg": slope,
        "aspect_deg": aspect
    })

    if (i + 1) % 1000 == 0:

        print(
            f"Processed {i + 1}/{total}"
        )


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

terrain = pd.DataFrame(results)

terrain.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# COVERAGE
# ------------------------------------------------------------

valid_elevation = terrain["elevation_m"].notna().sum()
valid_slope = terrain["slope_deg"].notna().sum()
valid_aspect = terrain["aspect_deg"].notna().sum()


print()
print("=" * 60)
print("TERRAIN EXTRACTION COMPLETE")
print("=" * 60)

print("Rows:", len(terrain))

print(
    f"Elevation coverage: "
    f"{valid_elevation}/{len(terrain)} "
    f"({valid_elevation / len(terrain) * 100:.2f}%)"
)

print(
    f"Slope coverage: "
    f"{valid_slope}/{len(terrain)} "
    f"({valid_slope / len(terrain) * 100:.2f}%)"
)

print(
    f"Aspect coverage: "
    f"{valid_aspect}/{len(terrain)} "
    f"({valid_aspect / len(terrain) * 100:.2f}%)"
)

print()
print("Output:")
print(OUTPUT_FILE)

print()
print(terrain.describe())