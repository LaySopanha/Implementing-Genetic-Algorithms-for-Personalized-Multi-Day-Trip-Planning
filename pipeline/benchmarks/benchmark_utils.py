import json
import random
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "backend" / "data" / "cleaned_merged_data.csv"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

df = pd.read_csv(DATA_FILE)
ID_LOOKUP = df.drop_duplicates(subset=["id"]).set_index("id", drop=False)
REVIEWS_MEDIAN = pd.to_numeric(df["num_reviews"], errors="coerce").median()
RATING_FALLBACK = pd.to_numeric(df["rating"], errors="coerce").median()

ACTIVITY_OPTIONS = {
    "Museum": "museum",
    "Aquarium": "aquarium",
    "Temple": "temple",
    "Park / Nature": "park_recreation_area",
    "Waterfall": "waterfall",
    "Beach": "beach",
    "Landmark": "landmark_attraction",
    "Art Gallery": "gallery",
    "Historical Site": "historical_monument",
    "Wildlife / Zoo": "wildlife_refuge",
    "Nightlife / Bars": "Night Club",
    "Coffee & Cafes": "cafe",
    "Local Markets": "food_market_stall",
}

ACTIVITY_CATEGORY_IDS = {
    "Beach": ["550-5510-0205"],
    "Aquarium": ["550-5520-0208"],
    "Park / Nature": ["550-5520-0354", "550-5510-0356"],
    "Waterfall": ["550-5510-0350"],
    "Wildlife / Zoo": ["550-5520-0210", "550-5520-0361"],
    "Museum": ["300-3100-0025", "300-3100-0029"],
    "Art Gallery": ["300-3000-0024"],
    "Historical Site": ["300-3200-0027", "300-3200-0030"],
    "Landmark": ["350-3500-0236", "350-3500-0246"],
    "Temple": ["300-3200-0286"],
    "Nightlife / Bars": ["600-6300-0067", "600-6300-0244"],
}


def timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_results_dir() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def summarize_series(values: Iterable[float]) -> dict:
    arr = np.array(list(values), dtype=float)
    return {
        "mean": round(float(np.mean(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
    }


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_markdown(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def get_supported_provinces(base_url: str) -> list[str]:
    return fetch_json(f"{base_url}/api/provinces")["provinces"]


def get_filters_for_province(base_url: str, province: str) -> dict:
    encoded = urllib.parse.quote(province)
    return fetch_json(f"{base_url}/api/activities/{encoded}")


def generate_trip(base_url: str, payload: dict) -> dict:
    return post_json(f"{base_url}/api/generate-trip", payload)


def eligible_provinces(base_url: str) -> list[str]:
    provinces = []
    for province in get_supported_provinces(base_url):
        try:
            filters = get_filters_for_province(base_url, province)
        except Exception:
            continue
        if filters.get("activities") and filters.get("accommodation") and filters.get("dining"):
            provinces.append(province)
    return provinces


def random_request(
    rng: random.Random,
    base_url: str,
    province: str | None = None,
    days: int = 3,
    per_day: int = 3,
    mode: str = "balanced",
) -> dict:
    province_choice = province or rng.choice(eligible_provinces(base_url))
    filters = get_filters_for_province(base_url, province_choice)

    activity_count = min(len(filters["activities"]), max(1, min(3, per_day)))
    return {
        "province": province_choice,
        "days": days,
        "activities": rng.sample(filters["activities"], k=activity_count),
        "accommodation": rng.sample(filters["accommodation"], k=1),
        "dining": rng.sample(filters["dining"], k=1),
        "perDay": per_day,
        "mode": mode,
    }


def flatten_activities(trip_response: dict) -> list[dict]:
    activities = []
    for day in trip_response["itinerary"]:
        activities.extend(day["activities"])
    return activities


def calculate_weighted_score(row) -> float:
    R = pd.to_numeric(row.get("rating"), errors="coerce")
    v = pd.to_numeric(row.get("num_reviews"), errors="coerce")

    if pd.isna(R):
        R = RATING_FALLBACK
    if pd.isna(v):
        v = 0

    m = REVIEWS_MEDIAN
    C = RATING_FALLBACK
    bayesian_avg = C if (v + m) == 0 else (v / (v + m)) * R + (m / (v + m)) * C
    volume_bonus = np.log10(v + 1) * 0.6
    return float((bayesian_avg * 0.4) + volume_bonus)


def candidate_activity_ids(request_payload: dict) -> set[str]:
    province = request_payload["province"]
    province_df = df[df["province"] == province]
    found_ids = set()

    for label in request_payload["activities"]:
        ontology_id = ACTIVITY_OPTIONS.get(label, label.lower())
        exact = province_df[province_df["ontologyId"] == ontology_id]
        found_ids.update(exact["id"].tolist())

        for category_id in ACTIVITY_CATEGORY_IDS.get(label, []):
            secondary = province_df[province_df["categories"].astype(str).str.contains(category_id, na=False)]
            found_ids.update(secondary["id"].tolist())

    return found_ids
