"""
Step 3: Train TF-IDF models and label encoders, then save to backend/model/.
Input:  data/processed/cleaned_merged_data.csv
Output: ../../backend/model/categories_tfidf_model.pkl
        ../../backend/model/description_tfidf_model.pkl
        ../../backend/model/label_encoders.pkl
"""

import logging
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "processed" / "cleaned_merged_data.csv"
MODEL_DIR = Path(__file__).parent.parent.parent / "backend" / "model"


def train_categories_model(df: pd.DataFrame) -> None:
    """TF-IDF on ontologyId + province — used for category-based recommendations."""
    df["combined"] = df["ontologyId"].astype(str) + " " + df["province"].astype(str)
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(df["combined"])

    out = MODEL_DIR / "categories_tfidf_model.pkl"
    with open(out, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "tfidf_matrix": matrix}, f)
    logger.info("Saved categories TF-IDF model → %s", out)


def train_description_model(df: pd.DataFrame) -> None:
    """TF-IDF on description column — used for description-based similarity."""
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(df["description"].fillna("Not available"))

    out = MODEL_DIR / "description_tfidf_model.pkl"
    with open(out, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "description_matrix": matrix}, f)
    logger.info("Saved description TF-IDF model → %s", out)


def train_label_encoders(df: pd.DataFrame) -> None:
    """Label encoders for ontologyId and province — used for filtering."""
    le_ontology = LabelEncoder()
    le_province = LabelEncoder()
    le_ontology.fit(df["ontologyId"].astype(str))
    le_province.fit(df["province"].astype(str))

    out = MODEL_DIR / "label_encoders.pkl"
    with open(out, "wb") as f:
        pickle.dump({"ontology": le_ontology, "province": le_province}, f)
    logger.info("Saved label encoders → %s", out)


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Training data not found: {DATA_FILE}\nRun the pipeline first.")

    df = pd.read_csv(DATA_FILE)
    logger.info("Loaded %d rows for training", len(df))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    train_categories_model(df)
    train_description_model(df)
    train_label_encoders(df)

    logger.info("All models saved to %s", MODEL_DIR)


if __name__ == "__main__":
    main()
