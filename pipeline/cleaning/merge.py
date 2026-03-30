"""
Step 2a: Merge HERE+TripAdvisor data with tourismcambodia.org scrape.
Input:  data/raw/tripadvisor_enriched.csv
        data/raw/tourism_cambodia.csv
Output: data/interim/merged_data.csv
"""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_FILE = Path(__file__).parent.parent / "data" / "raw" / "tripadvisor_enriched.csv"
SCRAPE_FILE = Path(__file__).parent.parent / "data" / "raw" / "tourism_cambodia.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "interim" / "merged_data.csv"


def main():
    api_df = pd.read_csv(API_FILE)
    scrape_df = pd.read_csv(SCRAPE_FILE)

    logger.info("API+TripAdvisor rows: %d", len(api_df))
    logger.info("Scrape rows: %d", len(scrape_df))

    # Normalize coordinates to numeric so the merge key is consistent
    for df in (api_df, scrape_df):
        for col in ("latitude", "longitude"):
            if col in df.columns:
                df[col] = df[col].replace("Not Available", pd.NA)
                df[col] = pd.to_numeric(df[col], errors="coerce")

    # Outer join on title + province to keep all records from both sources
    merged = pd.merge(api_df, scrape_df, on=["title", "province"], how="outer", suffixes=("", "_scrape"))

    # Prefer scraped description when the API description is missing
    if "description_scrape" in merged.columns:
        merged["description"] = merged.get("description", pd.NA).fillna(merged["description_scrape"])
        merged.drop(columns=["description_scrape"], inplace=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False)
    logger.info("Merged %d rows → %s", len(merged), OUTPUT_FILE)


if __name__ == "__main__":
    main()
