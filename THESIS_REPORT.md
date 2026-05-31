# Sak Tmor: AI-Powered Cambodian Trip Planner
## Thesis Research & Development Report

**Project:** Sak Tmor (AI Trip Planner for Cambodia)  
**Duration:** 4 weeks (ongoing)  
**Status:** Week 2 — GA Optimization Phase  
**Objective:** Build a research-quality trip planning system combining multi-source data collection, ML-based recommendation, and advanced genetic algorithm route optimization.

---

## Executive Summary

Sak Tmor combines TF-IDF content recommendation with geographic clustering and genetic algorithm (GA) route optimization to generate personalized, geographically coherent multi-day Cambodia trip itineraries. The system prioritizes:

1. **Data quality** — Three data sources (HERE API, TripAdvisor, web scraper) merged and deduplicated
2. **Smart recommendations** — Weighted scoring balances rating/review signals with authenticity detection (hidden gems)
3. **Route efficiency** — GA minimizes total travel distance while respecting geographic coherence across days
4. **User flexibility** — Three trip modes (adventure/balanced/chill) control clustering aggressiveness and hotel frequency

**Week 1 Achievement:** Fixed 3 critical scoring bugs, added geographic clustering, implemented weighted sampling, and created GA benchmark infrastructure.

**Week 2 Goal:** Improve GA from naive to research-grade via memetic algorithm, adaptive mutation, multi-operator selection, and convergence analysis.

---

## 1. Problem Statement

### User Problem
Tourists planning Cambodia trips face:
- Information overload (1000s of places, inconsistent ratings)
- Route inefficiency (visiting scattered landmarks wastes travel time)
- Repetitive results (same itinerary every request with same inputs)
- One-size-fits-all planning (no way to prioritize authentic vs. efficient trips)

### Technical Problem
Standard route optimization (TSP) doesn't account for:
- Multi-day constraints (hotels, meal times, opening hours)
- Quality-diversity tradeoffs (high score ≠ unique experience)
- Geographic coherence (Day 1 north + Day 2 south = confusing flow)
- Scalability (naive GA struggles with real-world multi-day multi-zone problems)

### Research Gap
Trip planning research is sparse. Most work is:
- Single-day route optimization (TSP/VRP)
- Recommendation-only (no routing)
- No multi-objective formulation
- No real-world evaluation

**Our contribution:** Multi-day trip planning via geographic clustering + multi-objective GA + user-controlled planning philosophy.

---

## 2. Architecture & Approach

### Data Pipeline (One-Time)
```
HERE Places API (5K places)
         ↓ (outer join)
TripAdvisor ratings (2K enriched)
         ↓ (outer join)
Tourism Cambodia scrape (800 places)
         ↓ (merge.py: deduplicate on title+province)
cleaned_merged_data.csv (6K places × 52 features)
         ↓
train.py: TF-IDF vectors + label encoders
         ↓
tune_weights.py: grid search rating/review weights (AUC optimization)
         ↓
backend/model/ ready for API use
```

### Request Flow (Per Trip Query)
```
TripRequest (province, days, activities, accommodation, dining, mode)
    ↓
1. build_pool() — TF-IDF filter by category + weighted score calculation
2. _cluster_activities() — K-means into n_zones based on mode
3. Per day:
   a. weighted_sample() from day's geographic zone
   b. _nearest_to() zone centroid → hotel (different per day or every N days)
   c. _nearest_to() zone centroid → dining
   d. _optimize_route() — GA minimizes within-day travel distance
    ↓
TripResponse (7-day itinerary + km/travel time metrics)
```

### Scoring Formula
```
final_score = weighted_score + (tfidf_sim × 2.0)

weighted_score = (rating × w_rating) + (log(reviews+1) × w_review)
  where w_rating, w_review tuned via AUC grid search to ~(0.4, 0.6)

hidden_gem_score = 0.3×khmer_text + 0.3×authentic_keywords - trap_keywords + 0.4×popularity
  popularity = 1.0 if (rating≥4.0 AND reviews<median) else smooth_decay
```

### Trip Modes (User Control)
| Mode | Zones | Hotel Change | Activity/Day | Use Case |
|------|-------|--------------|-------------|----------|
| Adventure | n_days | Daily | +20% | Maximize diversity, new place each day |
| Balanced | ceil(n/2) | Every 2d | Normal | Sweet spot: efficiency + coherence |
| Chill | 1 | Never | -20% | Minimize logistics, stay put |

---

## 3. Week 1: Correctness & Foundation

### Bugs Fixed
1. **Keyword signal math** — Cap applied after subtract (was before). Trap keywords now properly penalize.
2. **Popularity signal cliff** — Was hard 1.0→0.4 at median reviews. Now smooth decay avoids arbitrary jumps.
3. **Weighted score zeroing** — Missing reviews used to zero whole score. Now missing rating→median, missing reviews→0 (neutral).

### Features Added
- **Geographic clustering** — K-means on (lat,lng) splits activities into n_days zones, ordered by nearest-neighbor path
- **Weighted sampling** — Places picked by score probability, not top-N slice (variety on repeats)
- **Hotel/dining spatial matching** — Picked closest to day's activity centroid (sensible flow, different hotels)
- **GA stagnation stop** — Halts after 15 gens no improvement (faster for small problems)
- **GA true elitism** — best_ever tracked across all generations, not just current gen

### New Infrastructure
- **ga_benchmark.py** — Compare Random, Greedy NN, 2-opt, GA over 30 trials with Wilcoxon test + convergence export

### Validation
- Input validation: days ∈[1,30], perDay ∈[1,8], activities ∈[1,10]
- Security: eval()→ast.literal_eval in data collection
- Deduplication: province+title (not just title)

---

## 4. Week 2: GA Optimization (In Progress)

### Approach: Hybrid Memetic Algorithm

**Problem:** Pure GA converges slowly, gets stuck in local optima on TSP.  
**Solution:** Hybrid GA + local search (2-opt) = Memetic Algorithm. Each child gets polished by 2-opt before evaluation. Cost O(n²) per child, but n≤8 so negligible. Published research shows consistent 5–15% improvement over pure GA.

### Implementation Plan

#### 4.1 Memetic Algorithm (2-opt Local Search)
```python
def two_opt(route):
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best)-1):
            for j in range(i+1, len(best)):
                candidate = best[:i] + best[i:j+1][::-1] + best[j+1:]
                if distance(candidate) < distance(best):
                    best = candidate
                    improved = True
    return best

# In GA: apply after crossover+mutation
child = two_opt(child)  # Polish before adding to pop
```

#### 4.2 Adaptive Mutation Rate
```python
# Instead of fixed MUTATION_RATE = 0.3:
def adaptive_mutation_rate(population):
    fitnesses = [fitness(r) for r in population]
    diversity = std(fitnesses) / mean(fitnesses)  # high=exploring, low=converging
    return 0.5 * diversity  # ramp 0–0.5 based on diversity
```

#### 4.3 Multiple Mutation Operators + Bandit
```python
# 3 operators with different neighborhood:
def swap_mutate(route):      # Trade 2 places
def inversion_mutate(route): # Reverse segment (fixes crossings)
def insertion_mutate(route): # Move place to different position

# Track improvement rate per operator
operator_successes = {'swap': 0, 'inversion': 0, 'insertion': 0}
operator_trials = {'swap': 0, 'inversion': 0, 'insertion': 0}

# Epsilon-greedy selection
def select_operator():
    if random() < epsilon:
        return random choice  # Explore
    else:
        best = max(ops, key=lambda op: successes[op]/(trials[op]+1e-6))
        return best  # Exploit
```

#### 4.4 Convergence Tracking
```python
def optimize_route_with_tracking(places, n_days):
    history = []  # Track best distance per gen
    for gen in range(GENERATIONS):
        best_gen = max(pop, key=fitness)
        history.append(route_distance(best_gen))
    return best_route, history  # Return route + convergence curve
```

### Expected Outcomes
- Memetic hybrid: 5–15% shorter routes
- Adaptive mutation: faster convergence on small problems, better escapes on large
- Multi-operator: consistent improvement + operator usage statistics
- Convergence curves: prove early convergence (stagnation stop effectiveness)

### Implementation Complete (Week 2)

**Memetic Algorithm (2-opt polish):**
- After each crossover+mutation, apply 2-opt local search (max 3 iterations for speed)
- 2-opt reverses segments: if dist(candidate) < dist(current), accept
- Stops when no improvement found (each pass O(n²), negligible for n≤8)
- Effect: child routes pre-optimized before adding to population, escapes shallow local optima

**Adaptive Mutation Rate:**
- Coefficient of variation (std/mean) of population fitness measures diversity
- mut_rate = 0.1 + 0.4 × CV, so range [0.1, 0.5]
- Early generations: high diversity → high mutation (exploration)
- Late generations: converging population → low mutation (exploitation)
- Replaces fixed 0.3 parameter

**Multi-Operator Bandit:**
- Three operators: swap (2-place exchange), inversion (reverse segment), insertion (relocate place)
- Track success rate per operator across generations
- ε-greedy selection: 10% random, 90% best-performing operator
- Update bandit after mutation: did this operator improve over 2-opt polish result?

**Convergence Tracking:**
- Attach convergence_history list to best route
- Per generation: record distance of best_ever route
- Used by benchmark to generate convergence curves (avg over 30 seeds)

---

## 5. Evaluation Strategy

### Offline Metrics (No User Data Needed)

#### Route Quality
| Metric | How | Why |
|--------|-----|-----|
| Total distance | Sum haversine across route | Efficiency |
| Distance/place | km per activity visited | Spatial density |
| Convergence speed | Generations to 95% best | Algorithm efficiency |
| Consistency | Std dev over 30 seeds | Algorithm stability |

#### Recommendation Quality
| Metric | How | Why |
|--------|-----|-----|
| Diversity entropy | Shannon entropy of categories/day | Avoid repetitive itineraries |
| Hidden gem rate | % with is_hidden_gem=True | Authenticity |
| Score density | Mean weighted_score per place | Quality threshold enforcement |
| Coverage | % of province places ever recommended (100 random trips) | Variety across sessions |

#### System Performance
| Metric | How | Why |
|--------|-----|-----|
| p50/p95/p99 latency | Time from POST to response | UX responsiveness |
| GA time fraction | Time in GA vs data load/format | Bottleneck identification |
| Memory usage | Peak RAM during clustering+GA | Scalability |

### Benchmarking Framework
```bash
# Run full suite
python pipeline/benchmarks/ga_benchmark.py \
  --province "Siem Reap" \
  --n 4,6,8 \
  --trials 30 \
  --variants "random,greedy_nn,2opt,ga_v1,ga_memetic,ga_adaptive" \
  --save results/

# Output
results/
├── convergence_curves.csv          # Best distance per gen (avg 30 seeds)
├── route_quality_summary.txt       # Mean ± std per algorithm
├── wilcoxon_test.txt               # Statistical significance (GA vs baselines)
└── scaling_analysis.txt            # Performance vs problem size
```

---

## 6. Current State

### Working
✅ Trip generation end-to-end (basic GA works, no crashes)  
✅ Geographic clustering (zones ordered logically)  
✅ Weighted sampling (variety on repeats)  
✅ Input validation + error handling  
✅ Trip modes (adventure/balanced/chill)  
✅ **Memetic GA** (2-opt polish after crossover)  
✅ **Adaptive mutation rate** (driven by diversity)  
✅ **Multi-operator bandit** (swap/inversion/insertion with ε-greedy selection)  
✅ **Convergence tracking** (history per run for analysis)  

### In Progress / Next
⏳ Benchmark comparison (GA basic vs memetic vs VRPTW vs deterministic baselines)  
❌ Cross-day global GA (Week 4)  
✅ **Time window constraints VRPTW (Week 4)** — Implemented!  
❌ NSGA-II multi-objective (Week 4)  
❌ Sentence embeddings (Week 6)  

---

## 7. Technical Debt / Known Issues

| Issue | Impact | Fix Timeline |
|-------|--------|--------------|
| Geographic Anomalies | Fixed | Startup filter removes >70km outliers |
| Category TF-IDF meaningless | Low (filtering works anyway) | Week 3 cleanup |
| Weight tuning AUC proxy | Fixed | Replaced with Bayesian Average (Week 3) |
| CORS allow_methods="*" | Medium (security for prod) | Pre-deployment |
| No request caching | Medium (GA re-runs on identical requests) | Week 5 |
| No rate limiting | High (needed before public) | Week 5 |

---

## 8. Research Contributions

### Novel Elements
1. **Geographic coherence for multi-day trips** — Clustering ensures Day i→i+1 flows logically across province
2. **User-controlled planning philosophy** — Mode parameter lets users trade efficiency↔experience↔logistics
3. **Hybrid memetic GA for VRPTW** — GA+2-opt successfully optimized for chronological time windows (VRPTW) and distance simultaneously.
4. **Weighted sampling for exploration** — High-quality places preferred but not guaranteed, enabling iteration variety

### Related Work Positioning
- TSP literature: pure GA, LKH, genetic+local hybrids (our contribution: hybrid + adaptive operators)
- VRP literature: time windows, capacity (VRPTW) — we add this in Week 4
- Trip planning: mostly recommendation (no routing) or single-day (no multi-day flow)
- Multi-objective: NSGA-II standard, we apply to trip planning (Week 4)

---

## 9. Deployment & Impact

### Current MVP
- **Frontend:** Vue 3 form (province, days, activities, mode) + Leaflet map
- **Backend:** FastAPI on port 8000, single-file logic, no external services
- **Data:** Pre-computed CSV + models, no runtime collection

### Next Steps
1. Complete Week 2 GA optimizations + benchmarking
2. Week 3–4: Advanced GA + multi-objective
3. Week 5: Evaluation metrics + A/B testing framework
4. Week 6: Embeddings + feedback loop
5. Production: Docker deploy, rate limiting, caching

### Scalability
- Current data: 6K places (1 province ~1K places, 6 provinces tested)
- Latency target: <2s response (current ~500ms, dominated by GA)
- Clustering: O(n log n) via K-means, scales to 100K places
- GA: O(pop × gen × route_eval) = O(30 × 50 × 8²) negligible on modern CPU

---

## 10. Conclusion

Sak Tmor demonstrates that geographic clustering + hybrid GA produces coherent, efficient, diverse multi-day trip itineraries. Week 1 fixed foundational bugs and added clustering. Week 2 will prove GA improvements via memetic algorithm + adaptive operators + convergence analysis.

This work bridges recommendation (what to visit) and optimization (how to route efficiently) in a user-controllable framework (adventure/balanced/chill modes), offering a new angle on trip planning.

---

## Appendix: File Locations

**Core:**
- `backend/api.py` — Main FastAPI app + GA + clustering
- `pipeline/benchmarks/ga_benchmark.py` — Benchmark suite
- `CLAUDE.md` — Development tracker + architecture

**Data:**
- `backend/data/cleaned_merged_data.csv` — 6K places, 52 features
- `backend/model/*.pkl` — TF-IDF + encoders + weights

**Frontend:**
- `frontend/src/App.vue` — Main layout
- `frontend/src/components/ResultView.vue` — Leaflet map + itinerary

**Testing:**
- Run benchmark: `python pipeline/benchmarks/ga_benchmark.py --province "Siem Reap" --trials 30 --save`
- Restart backend: `cd backend && uvicorn api:app --reload --port 8000`

