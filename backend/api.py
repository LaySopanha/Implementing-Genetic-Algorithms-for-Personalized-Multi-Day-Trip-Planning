import ast
import json
import os
import random
from math import radians, sin, cos, sqrt, asin
from typing import List, Optional

import numpy as np
import pandas as pd
import pickle
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# ── Setup FastAPI App ──────────────────────────────────────────────────────────
app = FastAPI(title="Sak Tmor API", description="AI Trip Planner Backend", version="1.0.0")

# Allow requests from the Vue frontend.
# Local dev origins are always allowed; add the deployed frontend via the
# FRONTEND_ORIGIN env var (comma-separated for multiple, e.g. Vercel prod + preview).
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
allowed_origins += [o.strip() for o in os.getenv("FRONTEND_ORIGIN", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Load data ──────────────────────────────────────────────────────────────────
file_path = 'data/cleaned_merged_data.csv'
categories_tfidf_model_file_path = 'model/categories_tfidf_model.pkl'
label_encoders_file_path = 'model/label_encoders.pkl'
weights_file_path = 'model/weights.json'

print("Loading data and models...")
df = pd.read_csv(file_path)

with open(categories_tfidf_model_file_path, 'rb') as f:
    categories_model = pickle.load(f)
categories_vectorizer = categories_model['vectorizer']
categories_tfidf_matrix = categories_model['tfidf_matrix']

description_tfidf_model_file_path = 'model/description_tfidf_model.pkl'
try:
    with open(description_tfidf_model_file_path, 'rb') as f:
        description_model = pickle.load(f)
    description_vectorizer = description_model['vectorizer']
    description_tfidf_matrix = description_model['description_matrix']
    print("Loaded description TF-IDF model successfully.")
except FileNotFoundError:
    description_vectorizer = None
    description_tfidf_matrix = None
    print("Warning: description_tfidf_model.pkl not found. Description re-ranking will be skipped.")

with open(label_encoders_file_path, 'rb') as f:
    encoders = pickle.load(f)
label_encoder_ontology = encoders['ontology']
label_encoder_province = encoders['province']

# Load tuned scoring weights (falls back to defaults if tune_weights.py hasn't been run)
try:
    with open(weights_file_path) as f:
        _w = json.load(f)
    RATING_WEIGHT = float(_w.get('rating_weight', 0.4))
    REVIEW_WEIGHT = float(_w.get('review_weight', 0.6))
    print(f"Loaded tuned weights: rating={RATING_WEIGHT}, reviews={REVIEW_WEIGHT}")
except FileNotFoundError:
    RATING_WEIGHT, REVIEW_WEIGHT = 0.4, 0.6
    print("weights.json not found — using defaults (0.4 / 0.6). Run pipeline/training/tune_weights.py to tune.")

df['province_encoded'] = label_encoder_province.transform(df['province'])
df['ontology_encoded'] = label_encoder_ontology.transform(df['ontologyId'])

# Pre-parse lat/lng from the position column once at startup.
# Pools built from df will carry these columns, enabling geographic clustering at request time.
_lats, _lngs = [], []
for _pos in df['position']:
    if isinstance(_pos, str) and _pos.startswith('{'):
        try:
            _d = ast.literal_eval(_pos)
            _lats.append(float(_d.get('lat', float('nan'))))
            _lngs.append(float(_d.get('lng', float('nan'))))
            continue
        except Exception:
            pass
    _lats.append(float('nan'))
    _lngs.append(float('nan'))
df['_lat'] = _lats
df['_lng'] = _lngs

# Clean geographic anomalies: If a place is > ~70km (0.6 degrees) from its province median, mark it unroutable
_prov_medians = df.groupby('province')[['_lat', '_lng']].median()
for idx, row in df.iterrows():
    if pd.notna(row['_lat']) and pd.notna(row['_lng']):
        med_lat = _prov_medians.loc[row['province'], '_lat']
        med_lng = _prov_medians.loc[row['province'], '_lng']
        if abs(row['_lat'] - med_lat) > 0.6 or abs(row['_lng'] - med_lng) > 0.6:
            df.at[idx, '_lat'] = float('nan')
            df.at[idx, '_lng'] = float('nan')

# Precompute stats used at request time
TOP_ACTIVITY_KEYS = df['ontologyId'].value_counts().head(15).index.tolist()
REVIEWS_MEDIAN = pd.to_numeric(df['num_reviews'], errors='coerce').median()
RATING_FALLBACK = pd.to_numeric(df['rating'], errors='coerce').median()  # used when rating is missing

print("Data loaded gracefully!")

# ── Pydantic Models ────────────────────────────────────────────────────────────
# ── Trip mode configuration ───────────────────────────────────────────────────
# Controls clustering aggressiveness, hotel-change frequency, and activity density.
MODE_CONFIG = {
    #            n_zone_divisor  hotel_every  per_day_multiplier
    "adventure": (1,             1,           1.2),  # full clustering, hotel changes daily, more places
    "balanced":  (2,             2,           1.0),  # half as many zones, hotel every 2 days
    "chill":     (999,           999,         0.8),  # single zone, same hotel throughout, fewer places
}

class TripRequest(BaseModel):
    province: str
    days: int = Field(..., ge=1, le=30)
    activities: List[str] = Field(..., min_length=1, max_length=15)
    accommodation: List[str] = Field(..., min_length=1)
    dining: List[str] = Field(..., min_length=1)
    perDay: int = Field(default=3, ge=1, le=8)
    mode: str = Field(default="balanced")

class PlaceInfo(BaseModel):
    id: str
    title: str
    description: str
    category: str
    address: str
    rating: str
    reviews: str
    phone: str
    website: str
    image_url: str
    amenities: List[str]
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_hidden_gem: bool = False
    local_favored_score: float = 0.0
    open_time: float = 8.0   # Default 8:00 AM
    close_time: float = 18.0 # Default 6:00 PM

class DayPlan(BaseModel):
    day: int
    stays: List[PlaceInfo]
    dining: List[PlaceInfo]
    activities: List[PlaceInfo]
    distance_km: float = 0.0
    travel_time_min: int = 0  # estimated drive time at avg 40 km/h

class TripResponse(BaseModel):
    province: str
    total_days: int
    itinerary: List[DayPlan]

# ── Option Mappings (frontend label → ontologyId) ─────────────────────────────
ACTIVITY_OPTIONS = {
    "Museum":             ["museum", "Art Museum", "gallery", "theatre_music_culture", "history_museum"],
    "Aquarium":           ["aquarium", "Animal Park", "Water Park"],
    "Temple":             ["temple"],
    "Park / Nature":      ["park_recreation_area", "leisure_outdoor", "Outdoor-Recreation", "natural_geographical", "body_of_water", "River"],
    "Waterfall":          ["waterfall", "body_of_water", "natural_geographical", "River"],
    "Beach":              ["beach", "body_of_water", "natural_geographical"],
    "Landmark":           ["landmark_attraction", "tourist_attraction", "tourist-attraction", "historical_monument", "monument"],
    "Art Gallery":        ["gallery", "Art Museum", "theatre_music_culture"],
    "Historical Site":    ["historical_monument", "historical_site", "landmark_attraction", "tourist_attraction", "monument"],
    "Wildlife / Zoo":     ["wildlife_refuge", "wildlife-refuge", "Zoo", "Animal Park", "leisure_outdoor"],
    "Nightlife / Bars":   ["Night Club", "Nightlife-Entertainment", "Cocktail Lounge", "bar_pub", "Cocktail", "casino"],
    "Coffee & Cafes":     ["cafe", "coffee", "pastries"],
    "Local Markets":      ["food_market_stall", "pastries"],
}

# Secondary mapping: HERE category IDs → activity label
ACTIVITY_CATEGORY_IDS = {
    "Beach":           ["550-5510-0205"],
    "Aquarium":        ["550-5520-0208"],
    "Park / Nature":   ["550-5520-0354", "550-5510-0356"],
    "Waterfall":       ["550-5510-0350"],
    "Wildlife / Zoo":  ["550-5520-0210", "550-5520-0361"],
    "Museum":          ["300-3100-0025", "300-3100-0029"],
    "Art Gallery":     ["300-3000-0024"],
    "Historical Site": ["300-3200-0027", "300-3200-0030"],
    "Landmark":        ["350-3500-0236", "350-3500-0246"],
    "Temple":          ["300-3200-0286"],
    "Nightlife / Bars": ["600-6300-0067", "600-6300-0244", "600-6300-0066"], # Night Club, Cocktail Lounge, Pub
}

ACCOMMODATION_OPTIONS = {
    "Hotel":              ["hotel", "accommodation", "Lodging", "resort"],
    "Guesthouse":         ["guest_house", "accommodation", "Lodging", "bed_and_breakfast"],
    "Hostel":             ["hostel", "accommodation", "Lodging"],
    "Bed & Breakfast":    ["bed_and_breakfast", "accommodation", "guest_house"],
    "Motel":              ["motel", "accommodation", "Lodging"],
    "Holiday Park":       ["holiday_park", "accommodation", "leisure_outdoor"],
}

DINING_OPTIONS = {
    "Restaurant":         ["restaurant", "casual_dining", "Fine Dining", "fine_dining"],
    "Café":               ["cafe", "coffee", "pastries"],
    "Fine Dining":        ["fine_dining", "Fine Dining", "restaurant"],
    "Casual Dining":      ["casual_dining", "restaurant", "food_market_stall"],
    "Food Market / Stall":["food_market_stall", "casual_dining"],
}

# Keywords for precision and fallback discovery
KEYWORD_MAPPINGS = {
    "Market": ["Local Markets"],
    "Bar": ["Nightlife / Bars"],
    "Pub": ["Nightlife / Bars"],
    "Club": ["Nightlife / Bars"],
    "Cafe": ["Coffee & Cafes", "Café"],
    "Coffee": ["Coffee & Cafes", "Café"],
    "Inn": ["Guesthouse", "Hotel"],
    "Resort": ["Hotel", "Holiday Park"],
    "Beach": ["Beach"],
    "Waterfall": ["Waterfall"],
    "Pagoda": ["Temple"],
    "Wat": ["Temple"],
    "Museum": ["Museum"],
    "Gallery": ["Art Gallery"],
    "Park": ["Park / Nature"],
    "Zoo": ["Wildlife / Zoo"],
}

# ── Hidden Gem Detection ───────────────────────────────────────────────────────
# Three signals combined into a single local-favored probability (0–1):
#   1. Khmer text in description → likely written by local visitors
#   2. Authentic/local keywords in description
#   3. High rating with low review count vs. dataset median → undiscovered quality

_AUTHENTIC_KEYWORDS = ['authentic', 'local', 'hidden', 'off the beaten', 'undiscovered',
                       'secret', 'traditional', 'locals only', 'gem', 'peaceful', 'quiet']
_TOURIST_TRAP_KEYWORDS = ['tourist trap', 'overpriced', 'overcrowded', 'commercial', 'touristy']


def _khmer_text_percentage(text: str) -> float:
    """Calculate the percentage of Khmer Unicode characters in the text."""
    text_str = str(text)
    if not text_str:
        return 0.0
    khmer_chars = sum(1 for c in text_str if '\u1780' <= c <= '\u17FF')
    return min(1.0, (khmer_chars / len(text_str)) * 5)  # Scale up so 20% khmer = 1.0

# Precompute category frequencies for cross-province uniqueness
CATEGORY_FREQUENCIES = df['ontologyId'].value_counts(normalize=True).to_dict()

def _hidden_gem_score(row) -> tuple:
    """
    Returns (local_favored_score: float, is_hidden_gem: bool).
    Score >= 0.5 is classified as a hidden gem.
    """
    desc = str(row.get('description', '')).lower()

    # Signal 1: Khmer text percentage in description
    khmer_signal = _khmer_text_percentage(desc)

    # Signal 2: keyword analysis (authentic pushes up, tourist-trap language pulls down)
    authentic_hits = sum(1 for kw in _AUTHENTIC_KEYWORDS if kw in desc)
    trap_hits = sum(1 for kw in _TOURIST_TRAP_KEYWORDS if kw in desc)
    keyword_signal = max(0.0, min(1.0, (authentic_hits * 0.3) - (trap_hits * 0.5)))

    # Signal 3: Cross-province uniqueness (rarity of the category across the whole dataset)
    ontology_id = row.get('ontologyId', '')
    cat_freq = CATEGORY_FREQUENCIES.get(ontology_id, 1.0)
    # If category is very common (freq > 0.05), uniqueness is low. If rare, uniqueness is high.
    uniqueness_signal = max(0.0, 1.0 - (cat_freq * 20)) 

    # Signal 4: Recency (mentions of being new or recent years)
    recency_keywords = ['newly opened', 'recently opened', 'brand new', 'just opened', '2023', '2024', '2025']
    recency_hits = sum(1 for kw in recency_keywords if kw in desc)
    recency_signal = min(1.0, recency_hits * 0.5)

    # Signal 5: high rating + below-median review count
    rating = pd.to_numeric(row.get('rating'), errors='coerce')
    reviews = pd.to_numeric(row.get('num_reviews'), errors='coerce')
    popularity_signal = 0.0
    if pd.notna(rating) and pd.notna(reviews):
        if rating >= 4.0:
            # Smooth decay: fewer reviews than median -> closer to 1.0
            review_ratio = reviews / (REVIEWS_MEDIAN + 1)
            popularity_signal = max(0.0, 1.0 - (review_ratio * 0.6))

    # Weighted combination of all 5 signals
    score = (khmer_signal * 0.25) + (keyword_signal * 0.15) + (uniqueness_signal * 0.2) + (recency_signal * 0.15) + (popularity_signal * 0.25)
    return round(score, 3), score >= 0.5


# ── Genetic Algorithm Route Optimization ──────────────────────────────────────

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371

def _route_distance(places: list) -> float:
    """Sum of haversine distances along an ordered list of PlaceInfo. Used for pure distance display."""
    total = 0.0
    for i in range(len(places) - 1):
        a, b = places[i], places[i + 1]
        if a.lat and a.lng and b.lat and b.lng:
            total += _haversine(a.lat, a.lng, b.lat, b.lng)
    return total

def _route_cost(places: list) -> float:
    """Calculates distance plus time window penalties (VRPTW)."""
    total_dist = 0.0
    current_time = 8.0  # Start at 8:00 AM
    penalty = 0.0
    
    for i in range(len(places)):
        place = places[i]
        if i > 0:
            prev = places[i-1]
            if prev.lat and prev.lng and place.lat and place.lng:
                dist = _haversine(prev.lat, prev.lng, place.lat, place.lng)
                total_dist += dist
                current_time += dist / 40.0  # Assumed 40 km/h average speed
                
        # Time window checks
        if current_time < place.open_time:
            # Wait until it opens (small penalty for wasting time)
            penalty += (place.open_time - current_time) * 5.0
            current_time = place.open_time
        elif current_time > place.close_time:
            # Arrived after closing (massive penalty)
            penalty += (current_time - place.close_time) * 100.0
            
        current_time += 1.5  # Assumed 1.5 hours visit time
        
    return total_dist + penalty

def _optimize_route(places: list) -> list:
    """
    Genetic Algorithm (TSP/VRPTW) with memetic (GA+2-opt), adaptive mutation, multi-operator selection.
    Returns optimized route considering both distance and time windows.
    """
    routable = [p for p in places if p.lat and p.lng]
    unroutable = [p for p in places if not p.lat or not p.lng]

    if len(routable) <= 2:
        return routable + unroutable

    POP_SIZE = 30
    GENERATIONS = 50
    STAGNATION_LIMIT = 15
    EPSILON = 0.1  # multi-armed bandit exploration rate

    def fitness(route):
        cost = _route_cost(route)
        return 1 / cost if cost > 0 else float('inf')

    def tournament_select(pop):
        return max(random.sample(pop, 3), key=fitness)

    def ox1_crossover(p1, p2):
        n = len(p1)
        start, end = sorted(random.sample(range(n), 2))
        segment = p1[start:end]
        child = [None] * n
        child[start:end] = segment
        remaining = [x for x in p2 if x not in segment]
        idx = 0
        for j in range(n):
            if child[j] is None:
                child[j] = remaining[idx]
                idx += 1
        return child

    # ── Memetic: 2-opt local search (polish child) ──────────────────────────────
    def two_opt(route, max_iterations=10):
        """Quick 2-opt: reverse segments to reduce cost. O(n²) per pass."""
        best = route[:]
        best_cost = _route_cost(best)
        iterations = 0
        while iterations < max_iterations:
            improved = False
            for i in range(1, len(best) - 1):
                for j in range(i + 1, len(best)):
                    candidate = best[:i] + best[i:j+1][::-1] + best[j+1:]
                    cand_cost = _route_cost(candidate)
                    if cand_cost < best_cost - 1e-10:
                        best = candidate
                        best_cost = cand_cost
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break
            iterations += 1
        return best

    # ── Multi-operator mutation with bandit selection ────────────────────────────
    class OperatorBandit:
        def __init__(self):
            self.ops = {'swap': 0, 'inversion': 0, 'insertion': 0}
            self.successes = {'swap': 0, 'inversion': 0, 'insertion': 0}

        def select(self):
            if random.random() < EPSILON:
                return random.choice(list(self.ops.keys()))
            trials = self.ops
            rates = {op: self.successes[op] / (trials[op] + 1e-6) for op in self.ops}
            return max(rates, key=rates.get)

        def update(self, op, improved):
            self.ops[op] += 1
            if improved:
                self.successes[op] += 1

    bandit = OperatorBandit()

    def swap_mutate(route):
        if len(route) < 2:
            return route
        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
        return route

    def inversion_mutate(route):
        """Reverse a segment to fix crossings."""
        if len(route) < 3:
            return route
        start, end = sorted(random.sample(range(len(route)), 2))
        return route[:start] + route[start:end+1][::-1] + route[end+1:]

    def insertion_mutate(route):
        """Move a place to a different position."""
        if len(route) < 3:
            return route
        i = random.randint(0, len(route) - 1)
        j = random.randint(0, len(route) - 1)
        place = route.pop(i)
        route.insert(j, place)
        return route

    # ── Adaptive mutation rate ─────────────────────────────────────────────────────
    def get_mutation_rate(population):
        """Higher mutation when population is converging (low diversity)."""
        fitnesses = [fitness(r) for r in population]
        mean_fit = np.mean(fitnesses)
        std_fit = np.std(fitnesses)
        if mean_fit > 0:
            cv = std_fit / mean_fit  # coefficient of variation
            return 0.1 + 0.4 * cv   # ramp 0.1–0.5 based on diversity
        return 0.3

    # ── GA with memetic + adaptive mutation ─────────────────────────────────────
    population = [random.sample(routable, len(routable)) for _ in range(POP_SIZE)]

    best_ever = max(population, key=fitness)
    best_ever_fit = fitness(best_ever)
    stagnation = 0
    convergence_history = []

    for gen in range(GENERATIONS):
        best = max(population, key=fitness)
        best_fit = fitness(best)

        if best_fit > best_ever_fit:
            best_ever = best[:]
            best_ever_fit = best_fit
            stagnation = 0
        else:
            stagnation += 1
            if stagnation >= STAGNATION_LIMIT:
                break

        convergence_history.append(_route_distance(best_ever))

        mut_rate = get_mutation_rate(population)
        new_pop = [best_ever[:]]  # elitism

        while len(new_pop) < POP_SIZE:
            child = ox1_crossover(tournament_select(population), tournament_select(population))

            # Memetic: apply 2-opt local search to child
            old_dist = _route_distance(child)
            child = two_opt(child, max_iterations=3)
            new_dist = _route_distance(child)
            improved_by_2opt = new_dist < old_dist

            # Multi-operator mutation with bandit selection
            if random.random() < mut_rate:
                op = bandit.select()
                if op == 'swap':
                    child = swap_mutate(child[:])  # copy before mutate
                elif op == 'inversion':
                    child = inversion_mutate(child[:])
                else:  # insertion
                    child = insertion_mutate(child[:])
                # Track if mutation improved over 2-opt result
                mut_dist = _route_distance(child)
                improved_by_mut = mut_dist < new_dist
                bandit.update(op, improved_by_mut)

            new_pop.append(child)

        population = new_pop

    return best_ever + unroutable

# ── Core Recommendation Logic ──────────────────────────────────────────────────
def calculate_weighted_score(row):
    R = pd.to_numeric(row['rating'], errors='coerce')
    v = pd.to_numeric(row['num_reviews'], errors='coerce')
    
    if pd.isna(R) and pd.isna(v):
        return 0.0
        
    if pd.isna(R):
        R = RATING_FALLBACK
    if pd.isna(v):
        v = 0.0
        
    # Bayesian Average Rating
    # m = prior review count (using median of the dataset)
    # C = mean/median rating across the dataset
    m = REVIEWS_MEDIAN
    C = RATING_FALLBACK
    
    # Avoid division by zero if median is somehow 0, but REVIEWS_MEDIAN usually > 0
    if (v + m) == 0:
        bayesian_avg = C
    else:
        bayesian_avg = (v / (v + m)) * R + (m / (v + m)) * C
        
    # We still want places with massive numbers of reviews to get a slight boost 
    # to differentiate between a 4.5 with 10 reviews vs 4.5 with 1000 reviews
    # We can mix the Bayesian Average with a damped review volume score.
    volume_bonus = np.log10(v + 1) * REVIEW_WEIGHT
    
    return (bayesian_avg * RATING_WEIGHT) + volume_bonus

def get_recommendations(province_encoded, category_encoded):
    user_vector = categories_vectorizer.transform([str(category_encoded)])
    similarity_scores = cosine_similarity(user_vector, categories_tfidf_matrix)[0]
    recs = df[
        (df['ontology_encoded'] == category_encoded) &
        (df['province_encoded'] == province_encoded)
    ].copy()
    # Use actual row indices to assign the correct similarity score to each place
    recs['similarity_score'] = similarity_scores[recs.index]
    return recs.sort_values('similarity_score', ascending=False).head(100)

def build_pool(province_encoded, category_keys):
    pool = pd.DataFrame()
    try:
        encoded = label_encoder_ontology.transform(category_keys)
    except Exception as e:
        print(f"Failed to encode categories {category_keys}: {e}")
        return pool
    for enc in encoded:
        pool = pd.concat([pool, get_recommendations(province_encoded, enc)])

    if pool.empty:
        return pool

    pool['weighted_score'] = pool.apply(calculate_weighted_score, axis=1)
    
    # Use description TF-IDF for re-ranking
    if description_vectorizer is not None and description_tfidf_matrix is not None:
        query_str = " ".join(category_keys).replace('_', ' ')
        desc_vector = description_vectorizer.transform([query_str])
        desc_sim_scores = cosine_similarity(desc_vector, description_tfidf_matrix)[0]
        pool['desc_similarity_score'] = desc_sim_scores[pool.index]
    else:
        pool['desc_similarity_score'] = 0.0

    # Blend popularity score with TF-IDF similarity (similarity adds up to ~2 points)
    # Plus description similarity for re-ranking
    pool['final_score'] = pool['weighted_score'] + pool['similarity_score'] * 2.0 + pool['desc_similarity_score'] * 1.5
    return pool.drop_duplicates(subset=['id']).sort_values('final_score', ascending=False)

def format_place(r) -> PlaceInfo:
    """Takes a pandas Series (row) and formats it into a clean PlaceInfo model."""
    # Address parsing
    address = r['address'] if isinstance(r['address'], str) and r['address'] != 'Not available' else ""
    if address and address.startswith('{'):
        try:
            addr_dict = ast.literal_eval(address)
            address = addr_dict.get('label', address)
        except Exception:
            pass

    # Image logic
    category = str(r['ontologyId']).replace('_', ' ').title()
    img_url = r.get('image_src', '')
    if not isinstance(img_url, str) or 'http' not in img_url:
        img_url = '/placeholder-image.jpg'

    # Amenities parsing
    amenities = r.get('amenities', '')
    parsed_amenities = []
    if isinstance(amenities, str) and amenities not in ['Not available', 'Not Available', '[]']:
        try:
            amn_list = ast.literal_eval(amenities)
            if isinstance(amn_list, list):
                parsed_amenities = amn_list[:12]
        except Exception:
            pass

    # Coordinates parsing
    position = r.get('position', '')
    lat, lng = None, None
    if isinstance(position, str) and position.startswith('{'):
        try:
            pos_dict = ast.literal_eval(position)
            lat = float(pos_dict.get('lat'))
            lng = float(pos_dict.get('lng'))
        except Exception:
            pass

    # Time Window Parsing
    open_time = 8.0
    close_time = 18.0
    local_favored_score, is_hidden_gem = _hidden_gem_score(r)
    
    # If it's a hotel or guesthouse, they are basically 24/7 (or at least evening/morning)
    if 'hotel' in category.lower() or 'guest' in category.lower() or 'hostel' in category.lower():
        open_time = 0.0
        close_time = 24.0
    else:
        # Try TripAdvisor 'hours' first
        ta_hours_str = str(r.get('hours', ''))
        parsed = False
        if ta_hours_str != 'Not available' and '{' in ta_hours_str:
            try:
                ta_hours = ast.literal_eval(ta_hours_str)
                if 'periods' in ta_hours and len(ta_hours['periods']) > 0:
                    first_period = ta_hours['periods'][0]
                    if 'open' in first_period and 'time' in first_period['open']:
                        o_time = first_period['open']['time']
                        open_time = int(o_time[:2]) + int(o_time[2:4]) / 60.0
                    if 'close' in first_period and 'time' in first_period['close']:
                        c_time = first_period['close']['time']
                        close_time = int(c_time[:2]) + int(c_time[2:4]) / 60.0
                        if close_time < open_time: # closes past midnight
                            close_time += 24.0
                    parsed = True
            except Exception:
                pass
                
        # Fallback to HERE 'openingHours'
        if not parsed:
            here_hours_str = str(r.get('openingHours', ''))
            if here_hours_str != 'Not Available' and '[' in here_hours_str:
                try:
                    here_hours = ast.literal_eval(here_hours_str)
                    if isinstance(here_hours, list) and len(here_hours) > 0:
                        first_rule = here_hours[0]
                        if 'structured' in first_rule and len(first_rule['structured']) > 0:
                            s = first_rule['structured'][0]
                            start_str = s.get('start', '')
                            duration_str = s.get('duration', '')
                            if start_str.startswith('T') and len(start_str) >= 5:
                                open_time = int(start_str[1:3]) + int(start_str[3:5]) / 60.0
                                if duration_str.startswith('PT'):
                                    import re
                                    h_match = re.search(r'(\d+)H', duration_str)
                                    m_match = re.search(r'(\d+)M', duration_str)
                                    dur_h = int(h_match.group(1)) if h_match else 0
                                    dur_m = int(m_match.group(1)) if m_match else 0
                                    close_time = open_time + dur_h + dur_m / 60.0
                except Exception:
                    pass

    return PlaceInfo(
        id=str(r['id']),
        title=str(r['title']),
        description=str(r['description']) if str(r['description']) not in ['Not available', 'Not Available'] else "No description available.",
        category=category,
        address=address,
        rating=str(r['rating']) if str(r['rating']) != 'Not Available' else "No Rating",
        reviews=str(r['num_reviews']) if str(r['num_reviews']) != 'Not Available' else "0",
        phone=str(r.get('phone', '')) if str(r.get('phone', '')) != 'Not available' else "",
        website=str(r.get('website', '')) if str(r.get('website', '')) != 'Not available' else "",
        image_url=img_url,
        amenities=parsed_amenities,
        lat=lat,
        lng=lng,
        is_hidden_gem=is_hidden_gem,
        local_favored_score=local_favored_score,
        open_time=open_time,
        close_time=close_time
    )


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/provinces")
def get_supported_provinces():
    provinces = sorted(df['province'].unique().tolist())
    return {"provinces": provinces}

@app.get("/api/activities/{province}")
def get_filters_for_province(province: str):
    if province not in df['province'].values:
        raise HTTPException(status_code=400, detail=f"Province '{province}' not supported.")
    
    prov_df = df[df['province'] == province]
    
    def discover_available(options_map, category_ids_map=None):
        available = set()
        
        # 1. Broad matching by ontologyId
        for label, ontology_ids in options_map.items():
            for oid in ontology_ids:
                if not prov_df[prov_df['ontologyId'] == oid].empty:
                    available.add(label)
                    break
            
            # 2. Match by HERE category IDs
            if label not in available and category_ids_map and label in category_ids_map:
                for cat_id in category_ids_map[label]:
                    if prov_df['categories'].str.contains(cat_id, na=False).any():
                        available.add(label)
                        break
        
        # 3. Precision matching by Keywords in Title
        for kw, labels in KEYWORD_MAPPINGS.items():
            if prov_df['title'].str.contains(kw, case=False, na=False).any():
                for l in labels:
                    # Only add if it's relevant to the current options_map (Activities vs Stay vs Dine)
                    if l in options_map:
                        available.add(l)
        
        return sorted(list(available))

    return {
        "activities": discover_available(ACTIVITY_OPTIONS, ACTIVITY_CATEGORY_IDS),
        "accommodation": discover_available(ACCOMMODATION_OPTIONS),
        "dining": discover_available(DINING_OPTIONS)
    }

@app.post("/api/generate-trip", response_model=TripResponse)
def generate_trip_endpoint(req: TripRequest):
    province_str = req.province

    if province_str not in df['province'].values:
        raise HTTPException(status_code=400, detail=f"Province '{province_str}' not supported.")

    province_encoded = label_encoder_province.transform([province_str])[0]

    def flatten(l):
        return [item for sublist in l for item in (sublist if isinstance(sublist, list) else [sublist])]

    # Map frontend labels to ontologyId keys
    mapped_activities = flatten([ACTIVITY_OPTIONS.get(a, [a.lower()]) for a in req.activities])
    mapped_accom = flatten([ACCOMMODATION_OPTIONS.get(a, [a.lower()]) for a in req.accommodation])
    mapped_dining = flatten([DINING_OPTIONS.get(a, [a.lower()]) for a in req.dining])

    # Generate data pools for the entire trip
    activities_pool = build_pool(province_encoded, mapped_activities)
    stays_pool = build_pool(province_encoded, mapped_accom)
    dining_pool = build_pool(province_encoded, mapped_dining)

    # Fallback logic updated to handle lists
    def top_up_pool(pool, needed_count, fallback_options, current_mapped):
        if len(pool) < needed_count:
            # Flatten fallback options if they are lists of lists
            flat_fallbacks = flatten(fallback_options)
            for key in flat_fallbacks:
                if len(pool) >= needed_count:
                    break
                if key in current_mapped:
                    continue
                try:
                    more = build_pool(province_encoded, [key])
                    if not more.empty:
                        pool = pd.concat([pool, more]).drop_duplicates(subset=['id'])
                        pool['final_score'] = pool['final_score'].fillna(0)
                        pool = pool.sort_values('final_score', ascending=False)
                except Exception:
                    continue
        return pool

    activities_pool = top_up_pool(activities_pool, req.days * req.perDay, TOP_ACTIVITY_KEYS, mapped_activities)
    stays_pool = top_up_pool(stays_pool, req.days, list(ACCOMMODATION_OPTIONS.values()), mapped_accom)
    dining_pool = top_up_pool(dining_pool, req.days, list(DINING_OPTIONS.values()), mapped_dining)

    # ── Geographic clustering: split activities into n_days spatial zones ──────
    # Each day gets one zone so the itinerary flows geographically instead of
    # jumping across the province at random. Hotel and dining are then matched
    # to the centroid of that day's zone.

    def _weighted_sample(pool: pd.DataFrame, n: int, used_ids: set) -> pd.DataFrame:
        """Sample n rows from pool, weighted by final_score, excluding used_ids."""
        available = pool[~pool['id'].isin(used_ids)]
        if available.empty or n <= 0:
            return pd.DataFrame()
        n = min(n, len(available))
        weights = available['final_score'].clip(lower=0) + 1e-6
        weights = weights / weights.sum()
        chosen = np.random.choice(len(available), size=n, replace=False, p=weights.values)
        return available.iloc[sorted(chosen)]

    def _nearest_to(pool: pd.DataFrame, lat: float, lng: float, used_ids: set) -> pd.DataFrame:
        """Pick the single place in pool closest to (lat, lng), excluding used_ids."""
        available = pool[~pool['id'].isin(used_ids)]
        if available.empty:
            return pd.DataFrame()
        with_coords = available.dropna(subset=['_lat', '_lng'])
        if with_coords.empty:
            # No coordinates — fall back to weighted sample
            return _weighted_sample(available, 1, set())
        with_coords = with_coords.copy()
        with_coords['_dist'] = (with_coords['_lat'] - lat) ** 2 + (with_coords['_lng'] - lng) ** 2
        return with_coords.nsmallest(1, '_dist')

    def _cluster_activities(pool: pd.DataFrame, n_days: int) -> list:
        """
        Cluster activity pool into n_days geographic groups ordered by proximity.
        Returns a list of DataFrames (one per day) in geographic sequence.
        Falls back to even splitting when too few routable places exist.
        """
        valid = pool.dropna(subset=['_lat', '_lng']).copy()
        valid = valid[valid['_lat'].between(9.0, 15.5) & valid['_lng'].between(102.0, 108.0)]

        if len(valid) < n_days * 2:
            # Too sparse for meaningful clustering — split evenly
            chunk = max(1, len(pool) // n_days)
            return [pool.iloc[i * chunk:(i + 1) * chunk] for i in range(n_days)]

        n_clusters = min(n_days, len(valid))
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        valid['_cluster'] = km.fit_predict(valid[['_lat', '_lng']].values)
        centroids = km.cluster_centers_  # (n_clusters, 2): [lat, lng]

        # Order clusters geographically using nearest-neighbour on centroids
        # so Day 1 → Day 2 → Day 3 follows a logical path across the province
        order = [0]
        remaining = list(range(1, n_clusters))
        while remaining:
            last = centroids[order[-1]]
            nearest = min(
                remaining,
                key=lambda c: (centroids[c][0] - last[0]) ** 2 + (centroids[c][1] - last[1]) ** 2
            )
            order.append(nearest)
            remaining.remove(nearest)

        return [valid[valid['_cluster'] == c] for c in order]

    # ── Resolve mode settings ─────────────────────────────────────────────────
    zone_divisor, hotel_every, per_day_mult = MODE_CONFIG.get(req.mode, MODE_CONFIG["balanced"])
    effective_per_day = max(1, round(req.perDay * per_day_mult))

    # n_zones: adventure=n_days zones, balanced=ceil(n_days/2), chill=1
    n_zones = max(1, -(-req.days // zone_divisor))  # ceiling division
    day_clusters = _cluster_activities(activities_pool, n_zones)

    # Map each day to a cluster index (chill=all days share cluster 0)
    def _day_cluster(day_idx: int) -> pd.DataFrame:
        cluster_idx = min(day_idx // zone_divisor, len(day_clusters) - 1)
        return day_clusters[cluster_idx]

    used_activity_ids: set = set()
    used_stay_ids: set = set()
    used_dining_ids: set = set()
    current_stay_df: pd.DataFrame = pd.DataFrame()  # carry-over hotel for multi-day stays

    itinerary = []
    for day in range(1, req.days + 1):
        cluster = _day_cluster(day - 1)

        # Sample activities from this day's geographic zone
        day_act_df = _weighted_sample(cluster, effective_per_day, used_activity_ids)
        # Top up from full pool if zone was sparse
        if len(day_act_df) < effective_per_day:
            extra = _weighted_sample(
                activities_pool, effective_per_day - len(day_act_df),
                used_activity_ids | set(day_act_df['id'])
            )
            day_act_df = pd.concat([day_act_df, extra])

        # Compute centroid of today's sampled activities
        act_with_coords = day_act_df.dropna(subset=['_lat', '_lng'])
        if not act_with_coords.empty:
            centroid_lat = act_with_coords['_lat'].mean()
            centroid_lng = act_with_coords['_lng'].mean()
        else:
            centroid_lat = centroid_lng = None

        # Hotel: change on day 1 and every `hotel_every` days thereafter
        should_change_hotel = (day == 1) or ((day - 1) % hotel_every == 0)
        if should_change_hotel or current_stay_df.empty:
            if centroid_lat is not None:
                current_stay_df = _nearest_to(stays_pool, centroid_lat, centroid_lng, used_stay_ids)
            else:
                current_stay_df = _weighted_sample(stays_pool, 1, used_stay_ids)
            
            if not current_stay_df.empty and 'id' in current_stay_df.columns:
                used_stay_ids.update(current_stay_df['id'].tolist())
        day_stay_df = current_stay_df

        # Dining: always pick closest to today's zone (fresh each day)
        if centroid_lat is not None:
            day_dining_df = _nearest_to(dining_pool, centroid_lat, centroid_lng, used_dining_ids)
        else:
            day_dining_df = _weighted_sample(dining_pool, 1, used_dining_ids)

        used_activity_ids.update(day_act_df['id'].tolist() if not day_act_df.empty and 'id' in day_act_df.columns else [])
        used_dining_ids.update(day_dining_df['id'].tolist() if not day_dining_df.empty and 'id' in day_dining_df.columns else [])

        day_stays = [format_place(row) for _, row in day_stay_df.iterrows()]
        day_dining = [format_place(row) for _, row in day_dining_df.iterrows()]
        day_activities = [format_place(row) for _, row in day_act_df.iterrows()]

        # Optimize activity order using GA (TSP) to minimize travel distance
        day_activities = _optimize_route(day_activities)

        # Full day loop: hotel → activities → hotel (if hotel has valid coords)
        full_day_route = day_activities
        if day_stays and day_stays[0].lat and day_stays[0].lng:
            full_day_route = [day_stays[0]] + day_activities + [day_stays[0]]
        day_distance = round(_route_distance(full_day_route), 1)
        travel_time = max(1, round(day_distance / 40 * 60)) if day_distance > 0 else 0

        itinerary.append(DayPlan(
            day=day,
            stays=day_stays,
            dining=day_dining,
            activities=day_activities,
            distance_km=day_distance,
            travel_time_min=travel_time
        ))

    return TripResponse(
        province=province_str,
        total_days=req.days,
        itinerary=itinerary
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
