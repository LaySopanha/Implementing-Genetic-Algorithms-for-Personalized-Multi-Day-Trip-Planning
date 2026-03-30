"""
Step 2b: Clean and deduplicate the merged dataset.
Input:  data/interim/merged_data.csv
Output: data/processed/cleaned_merged_data.csv
        ../../backend/data/cleaned_merged_data.csv  (live copy for the API)
"""

import logging
import shutil
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = Path(__file__).parent.parent / "data" / "interim" / "merged_data.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "processed" / "cleaned_merged_data.csv"
BACKEND_DATA = Path(__file__).parent.parent.parent / "backend" / "data" / "cleaned_merged_data.csv"


def main():
    df = pd.read_csv(INPUT_FILE)
    logger.info("Loaded %d rows", len(df))

    # Drop duplicate places (same title keeps first occurrence)
    before = len(df)
    df.drop_duplicates(subset=["title"], keep="first", inplace=True)
    logger.info("Removed %d duplicates", before - len(df))

    # Normalize coordinates
    for col in ("latitude", "longitude"):
        if col in df.columns:
            df[col] = df[col].replace("Not Available", pd.NA)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with no usable location at all
    df.dropna(subset=["title"], inplace=True)

    # Fill remaining missing values
    df.fillna("Not available", inplace=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info("Cleaned dataset: %d rows → %s", len(df), OUTPUT_FILE)

    # Copy to backend so the API always has the latest data
    BACKEND_DATA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(OUTPUT_FILE, BACKEND_DATA)
    logger.info("Copied to backend: %s", BACKEND_DATA)


if __name__ == "__main__":
    main()
