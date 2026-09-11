import requests
import pandas as pd
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

WEATHER_DIR = BASE_DIR / "data" / "processed" / "weather"

WEATHER_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# IMD DISTRICT RAINFALL
# ============================================================

IMD_URL = (
    "https://mausam.imd.gov.in/"
    "api/districtwise_rainfall_api.php?id={}"
)


# ============================================================
# FETCH DISTRICT WEATHER
# ============================================================

def fetch_district_rainfall(district_id):

    url = IMD_URL.format(district_id)

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        if isinstance(data, dict):
            data = [data]

        df = pd.DataFrame(data)

        return df

    except Exception as e:

        print(
            "IMD rainfall request failed:",
            e
        )

        return None


# ============================================================
# SAVE WEATHER DATA
# ============================================================

def save_weather_data(df):

    if df is None or df.empty:
        return False

    output = (
        WEATHER_DIR
        / "imd_district_rainfall.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    return True


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("IMD WEATHER INTEGRATION TEST")
    print("=" * 60)

    # Example district ID.
    # Replace with the required IMD district object ID.
    district_id = 164

    print(
        "Requesting IMD rainfall data..."
    )

    df = fetch_district_rainfall(
        district_id
    )

    if df is None:

        print()
        print("IMD DATA NOT AVAILABLE")
        print()
        print(
            "The dashboard should use "
            "prototype scenario mode."
        )

    else:

        print()
        print(
            "IMD DATA RECEIVED"
        )

        print()
        print(
            df.head()
        )

        if save_weather_data(df):

            print()
            print(
                "Weather data saved successfully."
            )

    print("=" * 60)