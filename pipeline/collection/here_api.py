"""
Step 1a: Collect place data from HERE Discover Search API.
Output: data/raw/here_places.csv
"""

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_KEY = os.getenv("HERE_API_KEY")
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "here_places.csv"
CACHE_FILE = Path(__file__).parent / "here_cache.json"

KHMER_TO_ENGLISH = {
    "បន្ទាយមានជ័យ": "Banteay Meanchey",
    "បាត់ដំបង": "Battambang",
    "កំពង់ចាម": "Kampong Cham",
    "កំពង់ឆ្នាំង": "Kampong Chhnang",
    "កំពង់ស្ពឺ": "Kampong Speu",
    "កំពង់ធំ": "Kampong Thom",
    "កំពត": "Kampot",
    "កណ្ដាល": "Kandal",
    "កែប": "Kep",
    "កោះកុង": "Koh Kong",
    "ក្រចេះ": "Kratié",
    "មណ្ឌលគីរី": "Mondulkiri",
    "ឧត្តរមានជ័យ": "Oddar Meanchey",
    "បៃលិន": "Pailin",
    "ភ្នំពេញ": "Phnom Penh",
    "ព្រះសីហនុ": "Preah Sihanouk",
    "ព្រះវិហារ": "Preah Vihear",
    "ព្រៃវែង": "Prey Veng",
    "ពោធិ៍សាត់": "Pursat",
    "រតនគីរី": "Ratanakiri",
    "សៀមរាម": "Siem Reap",
    "ស្ទឹងត្រែង": "Stung Treng",
    "ស្វាយរៀង": "Svay Rieng",
    "តាកែវ": "Takéo",
    "ត្បូងឃ្មុំ": "Tboung Khmum",
}
ENGLISH_TO_KHMER = {v: k for k, v in KHMER_TO_ENGLISH.items()}

PROVINCE_COORDINATES = {
    "Phnom Penh": {"coordinates": "11.567881806331282,104.8640748481109", "radius": 23000},
    "Siem Reap": {"coordinates": "13.522455575367175,104.00609129009919", "radius": 83000},
    "Battambang": {"coordinates": "13.037084065077025,103.10293895070983", "radius": 100000},
    "Kampong Cham": {"coordinates": "12.130821225634246,105.28093939840798", "radius": 65000},
    "Kampong Chhnang": {"coordinates": "12.154884371833095,104.52505316142351", "radius": 53000},
    "Kampong Speu": {"coordinates": "11.552456281993676,104.28227297139938", "radius": 68000},
    "Kampong Thom": {"coordinates": "12.818297891048335,105.02002562101914", "radius": 91000},
    "Kandal": {"coordinates": "11.385377155237155,105.05503777120614", "radius": 63000},
    "Kep": {"coordinates": "10.533326515359832,104.34334813000457", "radius": 13000},
    "Kampot": {"coordinates": "10.811142083322647,104.29917691742993", "radius": 54000},
    "Kratié": {"coordinates": "12.680360440440909,106.10344148211848", "radius": 103000},
    "Koh Kong": {"coordinates": "11.53871159602269,103.35678202271257", "radius": 86000},
    "Mondulkiri": {"coordinates": "12.767844158835484,106.98714888740378", "radius": 99000},
    "Oddar Meanchey": {"coordinates": "14.163379821456678,103.81514749732268", "radius": 87000},
    "Pailin": {"coordinates": "12.89188362018884,102.62752697439433", "radius": 28000},
    "Preah Vihear": {"coordinates": "13.809695230628913,105.00774838185355", "radius": 100000},
    "Prey Veng": {"coordinates": "11.40195943645808,105.453426045157", "radius": 60000},
    "Pursat": {"coordinates": "12.320214538689978,103.66014632501194", "radius": 105000},
    "Ratanakiri": {"coordinates": "13.73330237247191,107.09398606248658", "radius": 118000},
    "Preah Sihanouk": {"coordinates": "10.927303417195487,103.84654246175806", "radius": 62000},
    "Stung Treng": {"coordinates": "13.783518512636956,106.20952280950144", "radius": 100000},
    "Svay Rieng": {"coordinates": "11.155586794609802,105.8449365400954", "radius": 55000},
    "Takéo": {"coordinates": "10.982244939023513,104.84922588388305", "radius": 53000},
    "Tboung Khmum": {"coordinates": "11.948814665664562,105.87494211102685", "radius": 70000},
    "Banteay Meanchey": {"coordinates": "13.688747621744977,103.03333017014755", "radius": 78000},
}

QUERIES = [
    "restaurant", "Food Market-Stall", "Fine Dining", "Casual Dining", "cafe",
    "Nightlife-Entertainment", "bar", "Night Club", "Cocktail Lounge",
    "Theatre, Music and Culture", "Performing Arts", "Casino",
    "museum", "tourist-attraction", "historic-site", "park",
    "Landmark-Attraction", "Gallery", "Historical Monument", "History Museum", "Art Museum",
    "Temple", "Body of Water", "Waterfall", "Bay-Harbor", "River", "Lake",
    "Mountain or Hill", "Mountain Passes", "Mountain Peaks",
    "Forest, Heath or Other Vegetation", "Natural and Geographical",
    "Lodging", "Hostel", "hotel", "motel", "guesthouse", "bed and breakfast",
    "Holiday Park", "Outdoor-Recreation", "Park-Recreation Area",
    "Beach", "Leisure", "Amusement Park", "Zoo", "Wild Animal Park",
    "Wildlife Refuge", "Aquarium", "Animal Park", "Water Park",
]

COLUMNS = [
    "title", "id", "language", "ontologyId", "address", "position",
    "access", "distance", "categories", "foodTypes", "references",
    "contacts", "openingHours", "province",
]


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def fetch_places(location: str, query: str, radius: int, province: str, cache: dict) -> list[dict]:
    khmer_province = ENGLISH_TO_KHMER.get(province, province)
    cache_key = f"{location}-{query}-{khmer_province}"

    if cache_key in cache:
        logger.info("Cache hit: %s", cache_key)
        return cache[cache_key]

    params = {
        "at": location,
        "q": query,
        "radius": radius,
        "apiKey": API_KEY,
        "limit": 100,
        "in": "countryCode:KHM",
        "county": khmer_province,
    }
    url = f"https://discover.search.hereapi.com/v1/discover?{urlencode(params)}"

    for attempt in range(5):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 429:
                wait = 2 ** attempt
                logger.warning("Rate limit, retrying in %ds", wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            items = response.json().get("items", [])
            cache[cache_key] = items
            _save_cache(cache)
            return items
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            time.sleep(2)

    return []


def process_item(item: dict, province: str) -> dict:
    khmer_province = item.get("address", {}).get("county", "")
    english_province = KHMER_TO_ENGLISH.get(khmer_province, province)
    return {
        "title": item.get("title", ""),
        "id": item.get("id", ""),
        "language": item.get("language", ""),
        "ontologyId": item.get("ontologyId", ""),
        "address": item.get("address", ""),
        "position": item.get("position", {}),
        "access": item.get("access", ""),
        "distance": item.get("distance", ""),
        "categories": item.get("categories", ""),
        "foodTypes": item.get("foodTypes", ""),
        "references": item.get("references", ""),
        "contacts": item.get("contacts", ""),
        "openingHours": item.get("openingHours", ""),
        "province": english_province,
    }


def save_to_csv(records: list[dict]) -> None:
    new_df = pd.DataFrame(records)[COLUMNS]
    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        df = pd.concat([existing, new_df], ignore_index=True)
    else:
        df = new_df
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info("Saved %d total records to %s", len(df), OUTPUT_FILE)


def main():
    if not API_KEY:
        raise EnvironmentError("HERE_API_KEY not set in .env")

    cache = _load_cache()
    all_records = []

    tasks = [
        (query, pdata["coordinates"], pdata["radius"], province)
        for province, pdata in PROVINCE_COORDINATES.items()
        for query in QUERIES
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_places, coords, query, radius, province, cache): (query, province)
            for query, coords, radius, province in tasks
        }
        for future in as_completed(futures):
            query, province = futures[future]
            try:
                items = future.result()
                all_records.extend(process_item(item, province) for item in items)
            except Exception as e:
                logger.error("Error for %s / %s: %s", query, province, e)

    if all_records:
        save_to_csv(all_records)
    else:
        logger.warning("No data collected.")


if __name__ == "__main__":
    main()
