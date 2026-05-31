"""
Image Enrichment Pipeline
=========================
Fetches the first photo for each place that:
  - has a valid TripAdvisor location_id
  - is currently missing image_src (value == 'Not available')

Uses TripAdvisor Content API: GET /location/{locationId}/photos
Updates cleaned_merged_data.csv in-place (saves a backup first).

Usage:
    python pipeline/collection/enrich_images.py [--limit N] [--dry-run]
"""

import argparse
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ── Setup ─────────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s"
)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent.parent / "backend" / "data" / "cleaned_merged_data.csv"
BACKUP_FILE = DATA_FILE.with_suffix(".csv.bak")

_raw_keys = os.getenv("TRIPADVISOR_API_KEYS", "")
API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]

_key_index = 0
_request_count = 0
_REQUESTS_PER_KEY = 5000  # TripAdvisor free tier limit per key


# ── API helpers ───────────────────────────────────────────────────────────────

def _get_api_key() -> str:
    global _key_index, _request_count
    if _request_count >= _REQUESTS_PER_KEY and _key_index + 1 < len(API_KEYS):
        _key_index += 1
        _request_count = 0
        logger.info("Switched to API key %d", _key_index + 1)
    return API_KEYS[_key_index]


def fetch_first_photo(location_id: str, retries: int = 3) -> str | None:
    """
    Call TripAdvisor Content API /location/{locationId}/photos
    Return the URL of the first medium/large image, or None.
    """
    global _request_count
    api_key = _get_api_key()
    url = (
        f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/photos"
        f"?key={api_key}&limit=1&language=en"
    )

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers={"accept": "application/json"},
                timeout=20
            )
            _request_count += 1

            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if not data:
                    return None
                # Try to get the largest available image variant
                images = data[0].get("images", {})
                for size in ("large", "medium", "original", "small", "thumbnail"):
                    img_obj = images.get(size)
                    if img_obj and img_obj.get("url"):
                        return img_obj["url"]
                return None

            elif resp.status_code == 429:
                wait = 60 * attempt
                logger.warning("Rate limit hit. Waiting %ds (attempt %d/%d)…", wait, attempt, retries)
                time.sleep(wait)

            elif resp.status_code == 404:
                logger.debug("location_id=%s not found (404)", location_id)
                return None

            else:
                logger.warning("HTTP %d for location_id=%s", resp.status_code, location_id)
                return None

        except requests.RequestException as exc:
            logger.warning("Request error for location_id=%s: %s", location_id, exc)
            if attempt < retries:
                time.sleep(5 * attempt)

    return None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _atomic_save(df: pd.DataFrame, path: Path) -> None:
    """Write df to a temp file in the same dir, then atomically replace target.
    This avoids PermissionError when the file is open in another process."""
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=".tmp_", suffix=".csv"
    )
    try:
        os.close(tmp_fd)
        df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, path)   # atomic on same filesystem
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Enrich image_src from TripAdvisor photos API")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum number of rows to process (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch URLs but do NOT save changes to CSV")
    args = parser.parse_args()

    if not API_KEYS:
        raise EnvironmentError(
            "TRIPADVISOR_API_KEYS not set in .env — "
            "set it as a comma-separated list of API keys."
        )

    logger.info("Loading dataset from %s …", DATA_FILE)
    df = pd.read_csv(DATA_FILE, low_memory=False)

    # Identify candidates: valid location_id, photo_count > 0, image_src missing
    needs_image_mask = (
        (df["image_src"] == "Not available") &
        (df["location_id"].notna()) &
        (df["location_id"] != "Not available") &
        (pd.to_numeric(df["photo_count"], errors="coerce").fillna(0) > 0)
    )
    candidates = df[needs_image_mask].copy()

    logger.info(
        "Found %d rows with a valid location_id and photo_count > 0 but no image.",
        len(candidates)
    )

    if args.limit:
        candidates = candidates.head(args.limit)
        logger.info("Processing first %d rows (--limit).", args.limit)

    # Backup before writing
    if not args.dry_run:
        shutil.copy2(DATA_FILE, BACKUP_FILE)
        logger.info("Backup saved to %s", BACKUP_FILE)

    fetched, updated, skipped = 0, 0, 0

    for idx, row in candidates.iterrows():
        loc_id = str(row["location_id"]).strip()
        name = row.get("title", f"row {idx}")

        photo_url = fetch_first_photo(loc_id)
        fetched += 1

        if photo_url:
            logger.info("[%d/%d] ✓ %s → %s", fetched, len(candidates), name, photo_url[:80])
            if not args.dry_run:
                df.at[idx, "image_src"] = photo_url
            updated += 1
        else:
            logger.info("[%d/%d] – %s → no photo found", fetched, len(candidates), name)
            skipped += 1

        # Small delay to be polite to the API (free tier = ~5 req/s)
        time.sleep(0.25)

        # Save progress every 50 rows
        if not args.dry_run and fetched % 50 == 0:
            _atomic_save(df, DATA_FILE)
            logger.info("  💾 Progress saved (%d/%d rows processed)", fetched, len(candidates))

    # Final save
    if not args.dry_run:
        _atomic_save(df, DATA_FILE)
        logger.info("✅ Done. %d updated, %d skipped. File saved.", updated, skipped)
    else:
        logger.info("✅ Dry-run complete. %d would be updated, %d skipped.", updated, skipped)


if __name__ == "__main__":
    main()
