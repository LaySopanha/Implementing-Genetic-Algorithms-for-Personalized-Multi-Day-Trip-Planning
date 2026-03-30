"""
Step 1b: Enrich HERE place data with TripAdvisor ratings, reviews, and details.
Input:  data/raw/here_places.csv
Output: data/raw/tripadvisor_enriched.csv
"""

import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Support multiple API keys to handle rate limits; set in .env as comma-separated values
# e.g. TRIPADVISOR_API_KEYS=key1,key2
_raw_keys = os.getenv("TRIPADVISOR_API_KEYS", "")
API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]

INPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "here_places.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "tripadvisor_enriched.csv"

_request_count = 0
_key_index = 0
_REQUESTS_PER_KEY = 5000


def _get_api_key() -> str:
    global _key_index, _request_count
    if _request_count >= _REQUESTS_PER_KEY and _key_index + 1 < len(API_KEYS):
        _key_index += 1
        _request_count = 0
        logger.info("Switched to API key %d", _key_index + 1)
    return API_KEYS[_key_index]


def get_location_id(place_name: str, latlng: str) -> str | None:
    global _request_count
    api_key = _get_api_key()
    url = (
        f"https://api.content.tripadvisor.com/api/v1/location/search"
        f"?key={api_key}&searchQuery={place_name}&latLong={latlng}&limit=1"
    )
    while True:
        try:
            response = requests.get(url, headers={"accept": "application/json"}, timeout=30)
            _request_count += 1
            if response.status_code == 200:
                data = response.json().get("data", [])
                return data[0]["location_id"] if data else None
            elif response.status_code == 429:
                logger.warning("Rate limit. Waiting 60s...")
                time.sleep(60)
            else:
                logger.error("Error %d for %s", response.status_code, place_name)
                return None
        except requests.RequestException as e:
            logger.error("Request failed for %s: %s", place_name, e)
            return None


def get_place_details(location_id: str) -> dict | None:
    global _request_count
    api_key = _get_api_key()
    url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/details?key={api_key}"
    while True:
        try:
            response = requests.get(url, headers={"accept": "application/json"}, timeout=30)
            _request_count += 1
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limit. Waiting 60s...")
                time.sleep(60)
            else:
                logger.error("Error %d for location %s", response.status_code, location_id)
                return None
        except requests.RequestException as e:
            logger.error("Request failed for location %s: %s", location_id, e)
            return None


def main():
    if not API_KEYS:
        raise EnvironmentError("TRIPADVISOR_API_KEYS not set in .env")

    places_df = pd.read_csv(INPUT_FILE)
    places_df["position"] = places_df["position"].apply(eval)
    places_df["latitude"] = places_df["position"].apply(lambda x: x.get("lat") if isinstance(x, dict) else None)
    places_df["longitude"] = places_df["position"].apply(lambda x: x.get("lng") if isinstance(x, dict) else None)

    file_exists = OUTPUT_FILE.exists()
    total = len(places_df)

    for i, row in places_df.iterrows():
        combined = row.to_dict()
        lat, lng = row.get("latitude"), row.get("longitude")

        if lat is not None and lng is not None:
            location_id = get_location_id(row["title"], f"{lat},{lng}")
            if location_id:
                details = get_place_details(location_id)
                if details:
                    combined.update(details)
        else:
            logger.warning("Skipping %s — no coordinates", row["title"])

        pd.DataFrame([combined]).to_csv(
            OUTPUT_FILE, mode="a", header=not file_exists, index=False
        )
        file_exists = True
        logger.info("[%d/%d] Processed %s", i + 1, total, row["title"])


if __name__ == "__main__":
    main()
