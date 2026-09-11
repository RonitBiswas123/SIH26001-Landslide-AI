import os
import gzip
import math
import requests
import numpy as np
import pandas as pd


INPUT = "data/processed/gsi_master_dataset.csv"
OUTPUT = "data/processed/gsi_terrain_dataset.csv"
TILE_DIR = "data/raw/dem/srtm_tiles"

os.makedirs(TILE_DIR, exist_ok=True)


def tile_name(lat, lon):
    lat_tile = math.floor(lat)
    lon_tile = math.floor(lon)

    ns = "N" if lat_tile >= 0 else "S"
    ew = "E" if lon_tile >= 0 else "W"

    return f"{ns}{abs(lat_tile):02d}{ew}{abs(lon_tile):03d}"


def download_tile(tile):

    hgt_path = os.path.join(TILE_DIR, tile + ".hgt")

    # Already downloaded
    if os.path.exists(hgt_path):
        return hgt_path

    ns = tile[0]
    lat = tile[1:3]
    ew = tile[3]
    lon = tile[4:7]

    url = (
        f"https://s3.amazonaws.com/elevation-tiles-prod/"
        f"skadi/{ns}{lat}{ew}{lon}/{tile}.hgt.gz"
    )

    print(f"Downloading {tile}...")

    try:

        response = requests.get(url, timeout=120)

        if response.status_code != 200:
            print(
                f"FAILED {tile}: "
                f"HTTP {response.status_code}"
            )
            return None

        gz_path = os.path.join(
            TILE_DIR,
            tile + ".hgt.gz"
        )

        with open(gz_path, "wb") as f:
            f.write(response.content)

        with gzip.open(gz_path, "rb") as f:
            data = f.read()

        with open(hgt_path, "wb") as f:
            f.write(data)

        os.remove(gz_path)

        return hgt_path

    except Exception as e:

        print(
            f"ERROR downloading {tile}: {e}"
        )

        return None


def load_tile(path):

    data = np.fromfile(
        path,
        dtype=">i2"
    )

    expected = 3601 * 3601

    if data.size != expected:
        raise ValueError(
            f"Invalid SRTM tile: {path}"
        )

    return data.reshape(
        (3601, 3601)
    )


def get_features(lat, lon, dem):

    lat_tile = math.floor(lat)
    lon_tile = math.floor(lon)

    # Convert coordinate to SRTM pixel
    row = round(
        (lat_tile + 1 - lat) * 3600
    )

    col = round(
        (lon - lon_tile) * 3600
    )

    # Need a 3x3 neighbourhood
    if (
        row < 1
        or row >= 3600
        or col < 1
        or col >= 3600
    ):
        return (
            np.nan,
            np.nan,
            np.nan,
            np.nan
        )

    window = dem[
        row - 1:row + 2,
        col - 1:col + 2
    ]

    # SRTM missing-data value
    if np.any(window == -32768):
        return (
            np.nan,
            np.nan,
            np.nan,
            np.nan
        )

    window = window.astype(float)

    elevation = window[1, 1]

    # Approximate SRTM resolution
    dy = 30.87
    dx = 30.87 * math.cos(
        math.radians(lat)
    )

    # Terrain derivatives
    dz_dx = (
        window[1, 2]
        - window[1, 0]
    ) / (2 * dx)

    dz_dy = (
        window[0, 1]
        - window[2, 1]
    ) / (2 * dy)

    # Slope
    slope_rad = math.atan(
        math.sqrt(
            dz_dx ** 2
            + dz_dy ** 2
        )
    )

    slope_deg = math.degrees(
        slope_rad
    )

    # Aspect
    aspect = math.degrees(
        math.atan2(
            dz_dx,
            dz_dy
        )
    )

    aspect = (
        aspect + 360
    ) % 360

    # Curvature
    d2z_dx2 = (
        window[1, 2]
        - 2 * window[1, 1]
        + window[1, 0]
    ) / (dx ** 2)

    d2z_dy2 = (
        window[0, 1]
        - 2 * window[1, 1]
        + window[2, 1]
    ) / (dy ** 2)

    curvature = (
        d2z_dx2
        + d2z_dy2
    )

    return (
        elevation,
        slope_deg,
        aspect,
        curvature
    )


def main():

    print("Loading GSI dataset...")

    df = pd.read_csv(INPUT)

    print(
        "Total landslide records:",
        len(df)
    )

    # Determine SRTM tile for every point
    df["tile"] = [
        tile_name(
            lat,
            lon
        )
        for lat, lon in zip(
            df["latitude"],
            df["longitude"]
        )
    ]

    tiles = df["tile"].unique()

    print(
        "Unique SRTM tiles:",
        len(tiles)
    )

    results = []

    for tile in tiles:

        tile_df = df[
            df["tile"] == tile
        ]

        path = download_tile(tile)

        if path is None:
            print(
                f"Skipping {tile}"
            )
            continue

        print(
            f"Processing {tile} "
            f"({len(tile_df)} points)"
        )

        try:

            dem = load_tile(path)

            for idx, row in tile_df.iterrows():

                (
                    elevation,
                    slope,
                    aspect,
                    curvature
                ) = get_features(
                    row["latitude"],
                    row["longitude"],
                    dem
                )

                results.append({
                    "index": idx,
                    "elevation_m": elevation,
                    "slope_deg": slope,
                    "aspect_deg": aspect,
                    "curvature": curvature
                })

            del dem

        except Exception as e:

            print(
                f"ERROR processing "
                f"{tile}: {e}"
            )

    terrain = pd.DataFrame(
        results
    )

    df = df.merge(
        terrain,
        left_index=True,
        right_on="index",
        how="left"
    )

    df.drop(
        columns=[
            "index",
            "tile"
        ],
        inplace=True
    )

    df.to_csv(
        OUTPUT,
        index=False
    )

    print()
    print("=" * 40)
    print("TERRAIN EXTRACTION COMPLETE")
    print("=" * 40)

    print(
        "Records:",
        len(df)
    )

    print(
        "Elevation available:",
        df["elevation_m"].notna().sum()
    )

    print(
        "Slope available:",
        df["slope_deg"].notna().sum()
    )

    print(
        "Aspect available:",
        df["aspect_deg"].notna().sum()
    )

    print(
        "Curvature available:",
        df["curvature"].notna().sum()
    )

    print()
    print("Saved:")
    print(OUTPUT)


if __name__ == "__main__":
    main()