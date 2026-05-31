# Sak Tmor: AI-Powered Cambodian Trip Planner

Sak Tmor is a research-quality trip planning system designed to generate personalized, geographically coherent, and efficient multi-day itineraries for Cambodia. It bridges the gap between content-based recommendation and route optimization.

## Project Overview

- **Core Objective:** Build a research-grade trip planner combining multi-source data, ML recommendations, and advanced Genetic Algorithm (GA) route optimization.
- **Main Technologies:**
    - **Backend:** FastAPI (Python), Scikit-learn (K-Means, TF-IDF), NumPy, Pandas.
    - **Frontend:** Vue 3, Vite, Leaflet (Map visualization), Axios.
    - **Optimization:** Hybrid Memetic Algorithm (Genetic Algorithm + 2-opt local search).
    - **Data:** CSV-based data lake enriched from HERE API, TripAdvisor, and web scraping.

## Architecture

1.  **Data Pipeline:**
    - `pipeline/collection/`: Scrapers and API connectors (HERE, TripAdvisor).
    - `pipeline/cleaning/`: Merging and deduplication logic.
    - `pipeline/training/`: TF-IDF model generation and weight tuning.
2.  **Backend (`/backend`):**
    - FastAPI application serving the recommendation and optimization engine.
    - Logic for geographic clustering (K-Means) and route optimization (Memetic GA).
3.  **Frontend (`/frontend`):**
    - Interactive UI for preference input (province, duration, activity types, trip mode).
    - Itinerary visualization with Leaflet maps.

## Building and Running

### Using Docker (Recommended)
The project is containerized with Docker Compose for easy setup.
```bash
docker-compose up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:80 (Nginx)

### Manual Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Pipeline & Benchmarks
```bash
# Run GA benchmarks to analyze convergence and efficiency
python pipeline/benchmarks/ga_benchmark.py --province "Siem Reap" --trials 30 --save
```

## Development Conventions

- **Algorithmic Focus:** Changes to the GA should be validated via `ga_benchmark.py`.
- **Data Integrity:** The `cleaned_merged_data.csv` is the source of truth for the API. Any changes to data collection must be reflected through the pipeline scripts.
- **Trip Modes:** The system supports three modes: `adventure`, `balanced`, and `chill`, which control clustering aggressiveness and hotel frequency.
- **Geographic Coherence:** Prioritize spatial density and logical flow (Day i -> Day i+1) in itinerary generation.

## Project Documentation
- `THESIS_REPORT.md`: Comprehensive research and development details.
- `project-re-analysis.md`: Detailed analysis of the project's current state and goals.
