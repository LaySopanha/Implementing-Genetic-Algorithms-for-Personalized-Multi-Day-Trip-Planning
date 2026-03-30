import numpy as np
import pandas as pd
import pickle
import ast
import random
from math import radians, sin, cos, sqrt, asin
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sklearn.metrics.pairwise import cosine_similarity

# ── Setup FastAPI App ──────────────────────────────────────────────────────────
app = FastAPI(title="Sak Tmor API", description="AI Trip Planner Backend", version="1.0.0")

# Allow requests from the Vue frontend (Vite default is 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data ──────────────────────────────────────────────────────────────────
file_path = 'data/cleaned_merged_data.csv'
categories_tfidf_model_file_path = 'model/categories_tfidf_model.pkl'
label_encoders_file_path = 'model/label_encoders.pkl'

print("Loading data and models...")
df = pd.read_csv(file_path)

with open(categories_tfidf_model_file_path, 'rb') as f:
    categories_model = pickle.load(f)
categories_vectorizer = categories_model['vectorizer']
categories_tfidf_matrix = categories_model['tfidf_matrix']

with open(label_encoders_file_path, 'rb') as f:
    encoders = pickle.load(f)
label_encoder_ontology = encoders['ontology']
label_encoder_province = encoders['province']

df['province_encoded'] = label_encoder_province.transform(df['province'])
df['ontology_encoded'] = label_encoder_ontology.transform(df['ontologyId'])
# Precompute top activity categories for fallback (avoid recomputing on every request)
TOP_ACTIVITY_KEYS = df['ontologyId'].value_counts().head(15).index.tolist()
print("Data loaded gracefully!")

# ── Pydantic Models ────────────────────────────────────────────────────────────
class TripRequest(BaseModel):
    province: str
    days: int
    activities: List[str]  # e.g ["museum", "temple"]
    accommodation: str     # e.g "hotel"
    dining: str            # e.g "restaurant"
    perDay: int = 3

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
    "Museum":             "museum",
    "Aquarium":           "aquarium",
    "Temple":             "temple",
    "Park / Nature":      "park_recreation_area",
    "Waterfall":          "waterfall",
    "Beach":              "beach",
    "Landmark":           "landmark_attraction",
    "Art Gallery":        "gallery",
    "Historical Site":    "historical_monument",
    "Wildlife / Zoo":     "wildlife_refuge",
}
ACCOMMODATION_OPTIONS = {
    "Hotel":              "hotel",
    "Guesthouse":         "guest_house",
    "Hostel":             "hostel",
    "Bed & Breakfast":    "bed_and_breakfast",
    "Motel":              "motel",
    "Holiday Park":       "holiday_park",
}
DINING_OPTIONS = {
    "Restaurant":         "restaurant",
    "Café":               "cafe",
    "Fine Dining":        "fine_dining",
    "Casual Dining":      "casual_dining",
    "Food Market / Stall":"food_market_stall",
}

# ── Genetic Algorithm Route Optimization ──────────────────────────────────────

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371

def _route_distance(places: list) -> float:
    """Sum of haversine distances along an ordered list of PlaceInfo."""
    total = 0.0
    for i in range(len(places) - 1):
        a, b = places[i], places[i + 1]
        if a.lat and a.lng and b.lat and b.lng:
            total += _haversine(a.lat, a.lng, b.lat, b.lng)
    return total

def _optimize_route(places: list) -> list:
    """
    Reorder places using a Genetic Algorithm (TSP) to minimize total travel distance.
    Places without coordinates are excluded from the GA and appended at the end.
    """
    routable = [p for p in places if p.lat and p.lng]
    unroutable = [p for p in places if not p.lat or not p.lng]

    if len(routable) <= 2:
        return routable + unroutable

    POP_SIZE = 30
    GENERATIONS = 50
    MUTATION_RATE = 0.3

    def fitness(route):
        d = _route_distance(route)
        return 1 / d if d > 0 else float('inf')

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

    def swap_mutate(route):
        if random.random() < MUTATION_RATE:
            i, j = random.sample(range(len(route)), 2)
            route[i], route[j] = route[j], route[i]
        return route

    population = [random.sample(routable, len(routable)) for _ in range(POP_SIZE)]

    for _ in range(GENERATIONS):
        best = max(population, key=fitness)
        new_pop = [best]
        while len(new_pop) < POP_SIZE:
            child = ox1_crossover(tournament_select(population), tournament_select(population))
            child = swap_mutate(child)
            new_pop.append(child)
        population = new_pop

    optimized = max(population, key=fitness)
    return optimized + unroutable

# ── Core Recommendation Logic ──────────────────────────────────────────────────
def calculate_weighted_score(row):
    if row['rating'] == 'Not Available' or row['num_reviews'] == 'Not Available':
        return 0
    rating = pd.to_numeric(row['rating'], errors='coerce')
    num_reviews = pd.to_numeric(row['num_reviews'], errors='coerce')
    if pd.isna(rating) or pd.isna(num_reviews):
        return 0
    return (rating * 0.4) + (np.log(num_reviews + 1) * 0.6)

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
    # Blend popularity score with TF-IDF similarity (similarity adds up to ~2 points)
    pool['final_score'] = pool['weighted_score'] + pool['similarity_score'] * 2.0
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
        lng=lng
    )


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/provinces")
def get_supported_provinces():
    provinces = sorted(df['province'].unique().tolist())
    return {"provinces": provinces}

@app.post("/api/generate-trip", response_model=TripResponse)
def generate_trip_endpoint(req: TripRequest):
    province_str = req.province

    if province_str not in df['province'].values:
        raise HTTPException(status_code=400, detail=f"Province '{province_str}' not supported.")

    province_encoded = label_encoder_province.transform([province_str])[0]

    # Map frontend labels to ontologyId keys
    mapped_activities = [ACTIVITY_OPTIONS.get(a, a.lower()) for a in req.activities]
    mapped_accom = ACCOMMODATION_OPTIONS.get(req.accommodation, req.accommodation.lower())
    mapped_dining = DINING_OPTIONS.get(req.dining, req.dining.lower())

    # Generate data pools for the entire trip
    activities_pool = build_pool(province_encoded, mapped_activities)
    stays_pool = build_pool(province_encoded, [mapped_accom])
    dining_pool = build_pool(province_encoded, [mapped_dining])

    # Fallback for activities if not enough
    total_needed = req.days * req.perDay
    if len(activities_pool) < total_needed:
        for key in TOP_ACTIVITY_KEYS:
            if len(activities_pool) >= total_needed:
                break
            if key in mapped_activities:
                continue
            try:
                more = build_pool(province_encoded, [key])
                if not more.empty:
                    activities_pool = pd.concat([activities_pool, more]).drop_duplicates(subset=['id'])
                    activities_pool['final_score'] = activities_pool['final_score'].fillna(0)
                    activities_pool = activities_pool.sort_values('final_score', ascending=False)
            except Exception:
                continue

    # Fallback for stays if the province has few accommodation options
    if len(stays_pool) < req.days:
        for key in ACCOMMODATION_OPTIONS.values():
            if key == mapped_accom:
                continue
            try:
                more = build_pool(province_encoded, [key])
                if not more.empty:
                    stays_pool = pd.concat([stays_pool, more]).drop_duplicates(subset=['id'])
                    stays_pool['final_score'] = stays_pool['final_score'].fillna(0)
                    stays_pool = stays_pool.sort_values('final_score', ascending=False)
            except Exception:
                continue

    # Fallback for dining if the province has few dining options
    if len(dining_pool) < req.days:
        for key in DINING_OPTIONS.values():
            if key == mapped_dining:
                continue
            try:
                more = build_pool(province_encoded, [key])
                if not more.empty:
                    dining_pool = pd.concat([dining_pool, more]).drop_duplicates(subset=['id'])
                    dining_pool['final_score'] = dining_pool['final_score'].fillna(0)
                    dining_pool = dining_pool.sort_values('final_score', ascending=False)
            except Exception:
                continue

    # Distribute the pools into days
    itinerary = []
    for day in range(1, req.days + 1):
        start = (day - 1) * req.perDay
        end = day * req.perDay

        day_stays = [format_place(row) for _, row in stays_pool.iloc[start:end].iterrows()]
        day_dining = [format_place(row) for _, row in dining_pool.iloc[start:end].iterrows()]
        day_activities = [format_place(row) for _, row in activities_pool.iloc[start:end].iterrows()]

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
