"""
Tune the scoring formula weights (rating vs. review count) using grid search.

Strategy: treat places in the top quartile of BOTH rating and num_reviews as
proxy "ground truth" quality places. Find the α, β (α + β = 1) that maximize
the AUC of separating quality from non-quality places using the scoring formula:
    score = α × rating_norm + β × log(reviews + 1)_norm

Saves results to backend/model/weights.json so api.py loads them at startup.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent.parent / "backend" / "data" / "cleaned_merged_data.csv"
WEIGHTS_FILE = Path(__file__).parent.parent.parent / "backend" / "model" / "weights.json"

DEFAULT_WEIGHTS = {"rating_weight": 0.4, "review_weight": 0.6}


def save_weights(alpha: float, beta: float) -> None:
    WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    weights = {"rating_weight": round(alpha, 2), "review_weight": round(beta, 2)}
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=2)
    logger.info("Weights saved → %s", WEIGHTS_FILE)


def main():
    df = pd.read_csv(DATA_FILE)

    df["rating_num"] = pd.to_numeric(df["rating"], errors="coerce")
    df["reviews_num"] = pd.to_numeric(df["num_reviews"], errors="coerce")
    df = df.dropna(subset=["rating_num", "reviews_num"])

    if len(df) < 100:
        logger.warning("Too few rated places (%d). Using default weights.", len(df))
        save_weights(**DEFAULT_WEIGHTS)
        return

    df["log_reviews"] = np.log(df["reviews_num"] + 1)

    # Normalize both signals to [0, 1]
    def norm(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-9)

    df["rating_norm"] = norm(df["rating_num"])
    df["log_reviews_norm"] = norm(df["log_reviews"])

    # Proxy ground truth: top 25% of both rating AND reviews
    q75_rating = df["rating_num"].quantile(0.75)
    q75_reviews = df["reviews_num"].quantile(0.75)
    df["is_quality"] = (
        (df["rating_num"] >= q75_rating) & (df["reviews_num"] >= q75_reviews)
    ).astype(int)

    logger.info(
        "Rated places: %d | Quality places (top-quartile both): %d (%.1f%%)",
        len(df),
        df["is_quality"].sum(),
        df["is_quality"].mean() * 100,
    )

    # Grid search over α in steps of 0.05
    results = []
    for alpha in np.arange(0.05, 1.0, 0.05):
        beta = 1.0 - alpha
        scores = alpha * df["rating_norm"] + beta * df["log_reviews_norm"]
        try:
            auc = roc_auc_score(df["is_quality"], scores)
            results.append((round(float(alpha), 2), round(float(auc), 4)))
        except Exception:
            pass

    if not results:
        logger.warning("Grid search failed. Using defaults.")
        save_weights(**DEFAULT_WEIGHTS)
        return

    results.sort(key=lambda x: x[1], reverse=True)
    best_alpha, best_auc = results[0]

    logger.info("\nTop 5 weight combinations:")
    for alpha, auc in results[:5]:
        logger.info("  rating=%.2f  reviews=%.2f  →  AUC=%.4f", alpha, 1 - alpha, auc)

    logger.info(
        "\nBest: rating=%.2f  reviews=%.2f  (AUC=%.4f)",
        best_alpha, 1 - best_alpha, best_auc,
    )

    save_weights(best_alpha, 1.0 - best_alpha)


if __name__ == "__main__":
    main()
