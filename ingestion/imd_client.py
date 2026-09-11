import requests
import os
import json

BASE_URL = "https://api.imd.gov.in/api/v1"

OUTPUT_DIR = "data/raw/imd"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_json(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"

    print(f"\nRequesting: {url}")

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    print("HTTP:", response.status_code)

    response.raise_for_status()

    return response.json()


def save_json(data, filename):
    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("Saved:", path)


def main():

    print("=" * 60)
    print("IMD API CONNECTION")
    print("=" * 60)

    try:

        # Test the current weather endpoint.
        # No station ID is supplied initially.
        data = get_json("current_wx")

        save_json(
            data,
            "current_weather.json"
        )

        print("\nIMD API is working.")

        if isinstance(data, dict):
            print(
                "Response keys:",
                list(data.keys())
            )

        elif isinstance(data, list):
            print(
                "Records returned:",
                len(data)
            )

    except Exception as e:

        print("\nIMD API ERROR:")
        print(e)


if __name__ == "__main__":
    main()