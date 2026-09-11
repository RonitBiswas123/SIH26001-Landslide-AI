import os
import math
import time
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


INPUT_FILE = "data/processed/gsi_district_mapped.csv"
DEM_DIR = "data/raw/dem"

os.makedirs(DEM_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

print("=" * 60)
print("COPERNICUS DEM DOWNLOADER")
print("=" * 60)

print(f"Landslide records : {len(df)}")
print(f"Unique coordinates: {df[['latitude','longitude']].drop_duplicates().shape[0]}")


# ------------------------------------------------------------
# GET REQUIRED 1-DEGREE TILES
# ------------------------------------------------------------

tiles = set()

for _, row in df.iterrows():

    lat = math.floor(float(row["latitude"]))
    lon = math.floor(float(row["longitude"]))

    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"

    tile = (
        f"{ns}{abs(lat):02d}"
        f"{ew}{abs(lon):03d}"
    )

    tiles.add(tile)

tiles = sorted(tiles)

print(f"Required DEM tiles: {len(tiles)}")


# ------------------------------------------------------------
# DOWNLOAD FUNCTION
# ------------------------------------------------------------

def download_tile(tile):

    lat = int(tile[1:3])
    lon = int(tile[4:7])

    ns = tile[0]
    ew = tile[3]

    folder = (
        f"Copernicus_DSM_COG_10_"
        f"{ns}{lat:02d}_00_"
        f"{ew}{lon:03d}_00_DEM"
    )

    filename = folder + ".tif"

    url = (
        "https://copernicus-dem-30m.s3.amazonaws.com/"
        + folder + "/"
        + filename
    )

    output = os.path.join(
        DEM_DIR,
        tile + ".tif"
    )

    # Already downloaded
    if os.path.exists(output):

        size = os.path.getsize(output)

        if size > 1_000_000:

            return tile, "EXISTS", size

        else:

            os.remove(output)

    # Retry up to 3 times
    for attempt in range(3):

        try:

            print(f"Downloading {tile}...")

            response = requests.get(
                url,
                stream=True,
                timeout=120
            )

            if response.status_code != 200:

                return (
                    tile,
                    f"HTTP {response.status_code}",
                    0
                )

            temp = output + ".part"

            with open(temp, "wb") as f:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if chunk:

                        f.write(chunk)

            size = os.path.getsize(temp)

            # Basic validation
            if size < 1_000_000:

                os.remove(temp)

                raise ValueError(
                    "Downloaded file is too small"
                )

            os.replace(temp, output)

            return tile, "OK", size

        except Exception as e:

            print(
                f"{tile} attempt {attempt + 1} failed: {e}"
            )

            time.sleep(2)

    return tile, "FAILED", 0


# ------------------------------------------------------------
# DOWNLOAD IN PARALLEL
# ------------------------------------------------------------

print()
print("Starting parallel download...")
print("Workers: 6")
print()

results = []

with ThreadPoolExecutor(max_workers=6) as executor:

    futures = {
        executor.submit(download_tile, tile): tile
        for tile in tiles
    }

    completed = 0

    for future in as_completed(futures):

        result = future.result()

        results.append(result)

        completed += 1

        tile, status, size = result

        print(
            f"[{completed}/{len(tiles)}] "
            f"{tile}: {status} "
            f"({size / 1024 / 1024:.1f} MB)"
        )


# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print()
print("=" * 60)
print("DOWNLOAD COMPLETE")
print("=" * 60)

success = sum(
    1 for _, status, _ in results
    if status in ["OK", "EXISTS"]
)

failed = len(results) - success

print(f"Successful: {success}")
print(f"Failed    : {failed}")

if failed:

    print()
    print("Failed tiles:")

    for tile, status, _ in results:

        if status not in ["OK", "EXISTS"]:

            print(
                f"  {tile}: {status}"
            )

else:

    print()
    print("ALL DEM TILES DOWNLOADED SUCCESSFULLY.")

print()
print(f"DEM directory: {DEM_DIR}")