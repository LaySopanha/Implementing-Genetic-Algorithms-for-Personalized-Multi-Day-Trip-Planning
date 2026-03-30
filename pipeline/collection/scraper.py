"""
Step 1c: Scrape attraction descriptions from tourismcambodia.org.
Output: data/raw/tourism_cambodia.csv
"""

import logging
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "tourism_cambodia.csv"

PROVINCE_URLS = [
    ("Phnom Penh", "https://tourismcambodia.org/provinces/44/phnom-penh-capital-city"),
    ("Ratanakiri", "https://tourismcambodia.org/provinces/45/rattanakiri"),
    ("Mondulkiri", "https://tourismcambodia.org/provinces/46/mondulkiri"),
    ("Siem Reap", "https://tourismcambodia.org/provinces/47/siem-reap"),
    ("Preah Sihanouk", "https://tourismcambodia.org/provinces/48/preah-sihanouk"),
    ("Stung Treng", "https://tourismcambodia.org/provinces/49/stung-treng"),
    ("Kratié", "https://tourismcambodia.org/provinces/50/kratie"),
    ("Preah Vihear", "https://tourismcambodia.org/provinces/51/preah-vihear"),
    ("Kampot", "https://tourismcambodia.org/provinces/52/kampot"),
    ("Kep", "https://tourismcambodia.org/provinces/53/kep"),
    ("Koh Kong", "https://tourismcambodia.org/provinces/54/koh-kong"),
    ("Kampong Thom", "https://tourismcambodia.org/provinces/55/kampong-thom"),
    ("Kandal", "https://tourismcambodia.org/provinces/56/kandal"),
    ("Takéo", "https://tourismcambodia.org/provinces/57/takeo"),
    ("Battambang", "https://tourismcambodia.org/provinces/58/battambang"),
    ("Kampong Cham", "https://tourismcambodia.org/provinces/59/kampong-cham"),
    ("Kampong Chhnang", "https://tourismcambodia.org/provinces/60/kampong-chhnang"),
    ("Kampong Speu", "https://tourismcambodia.org/provinces/61/kampong-speu"),
    ("Pursat", "https://tourismcambodia.org/provinces/62/pursat"),
    ("Oddar Meanchey", "https://tourismcambodia.org/provinces/63/oddar-meanchey"),
    ("Pailin", "https://tourismcambodia.org/provinces/64/pailin"),
    ("Prey Veng", "https://tourismcambodia.org/provinces/65/prey-veng"),
    ("Svay Rieng", "https://tourismcambodia.org/provinces/66/svay-rieng"),
    ("Banteay Meanchey", "https://tourismcambodia.org/provinces/67/banteay-meanchey"),
    ("Tboung Khmum", "https://tourismcambodia.org/provinces/245/tbong-khmum"),
]


def scrape_province(province: str, url: str) -> list[dict]:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Build lookup for hidden detail sections
    hidden_sections = {
        section.get("id"): section
        for section in soup.find_all("section", style="display: none;")
        if section.get("id")
    }

    section = soup.find("section", id=lambda x: x and x.startswith("section-"))
    if not section:
        logger.warning("No attraction section found for %s", province)
        return []

    records = []
    for item in section.find_all("li", class_="media"):
        img_tag = item.find("img")
        link_tag = item.find("a", class_="view-more")
        title_tag = item.find("h4", class_="body-title")
        desc_tag = item.find("p")

        description = desc_tag.text.strip() if desc_tag else ""

        # Prefer description from hidden detail section if available
        data_id = link_tag.get("data-id") if link_tag else None
        if data_id:
            hidden = hidden_sections.get(f"section-{data_id}")
            if hidden:
                hidden_p = hidden.find("p")
                if hidden_p:
                    description = hidden_p.text.strip()

        records.append({
            "title": title_tag.text.strip() if title_tag else "",
            "province": province,
            "description": description,
            "image_src": img_tag["src"] if img_tag else "",
            "link": link_tag["href"] if link_tag else "",
        })

    logger.info("Scraped %d attractions from %s", len(records), province)
    return records


def main():
    all_records = []
    for province, url in PROVINCE_URLS:
        all_records.extend(scrape_province(province, url))

    if all_records:
        df = pd.DataFrame(all_records)
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info("Saved %d records to %s", len(df), OUTPUT_FILE)
    else:
        logger.warning("No data scraped.")


if __name__ == "__main__":
    main()
