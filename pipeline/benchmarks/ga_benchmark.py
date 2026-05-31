"""
GA Benchmark: Compare routing algorithms on the Sak Tmor trip planning problem.

Algorithms compared:
  1. Random         — random permutation (lower bound baseline)
  2. Greedy NN      — nearest-neighbor heuristic (fast practical baseline)
  3. 2-opt          — local search only (strong deterministic baseline)
  4. GA (basic)     — GA with elitism + stagnation stop (Week 1)
  5. GA (memetic)   — GA + 2-opt + adaptive mutation + multi-operator bandit (Week 2)

Metrics (over 30 trials per test case):
  - Route distance (km): mean ± std
  - Computation time (ms): mean ± std
  - For GA variants: convergence curve (best distance per generation, averaged over trials)

Statistical test: Wilcoxon signed-rank test (GA memetic vs GA basic).

Usage:
  python pipeline/benchmarks/ga_benchmark.py
  python pipeline/benchmarks/ga_benchmark.py --province "Siem Reap" --n 6 --trials 50
"""

import argparse
import random
import time
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    from scipy.stats import wilcoxon
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[warn] scipy not installed — Wilcoxon test will be skipped. pip install scipy")

# ── Data paths ────────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent.parent / "data" / "processed" / "cleaned_merged_data.csv"
RESULTS_DIR = Path(__file__).parent / "results"


# ── Minimal place representation (no FastAPI dependency) ─────────────────────
@dataclass
class Place:
    title: str
    lat: float
    lng: float
    province: str
    category: str


# ── Distance utilities ────────────────────────────────────────────────────────
def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371


def route_distance(places: list[Place]) -> float:
    total = 0.0
    for i in range(len(places) - 1):
        total += haversine(places[i].lat, places[i].lng, places[i + 1].lat, places[i + 1].lng)
    return total


# ── Algorithm 1: Random ───────────────────────────────────────────────────────
def algo_random(places: list[Place], seed: int) -> tuple[list[Place], float, list]:
    rng = random.Random(seed)
    route = places[:]
    rng.shuffle(route)
    return route, route_distance(route), []


# ── Algorithm 2: Greedy Nearest-Neighbor ─────────────────────────────────────
def algo_greedy_nn(places: list[Place], seed: int) -> tuple[list[Place], float, list]:
    """Start from a random place, always go to the nearest unvisited place."""
    rng = random.Random(seed)
    unvisited = places[:]
    rng.shuffle(unvisited)  # random start
    route = [unvisited.pop(0)]
    while unvisited:
        last = route[-1]
        nearest = min(unvisited, key=lambda p: haversine(last.lat, last.lng, p.lat, p.lng))
        route.append(nearest)
        unvisited.remove(nearest)
    return route, route_distance(route), []


# ── Algorithm 3: 2-opt Local Search ──────────────────────────────────────────
def two_opt(route: list[Place]) -> list[Place]:
    """Iteratively reverse segments that reduce total distance. O(n²) per pass."""
    improved = True
    best = route[:]
    best_dist = route_distance(best)
    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                d = route_distance(candidate)
                if d < best_dist - 1e-10:
                    best = candidate
                    best_dist = d
                    improved = True
    return best


def algo_2opt(places: list[Place], seed: int) -> tuple[list[Place], float, list]:
    rng = random.Random(seed)
    start = places[:]
    rng.shuffle(start)
    route = two_opt(start)
    return route, route_distance(route), []


# ── Algorithm 4: Genetic Algorithm (matching api.py implementation) ───────────
def algo_ga(
    places: list[Place],
    seed: int,
    pop_size: int = 30,
    generations: int = 50,
    mutation_rate: float = 0.3,
    stagnation_limit: int = 15,
    record_convergence: bool = True,
) -> tuple[list[Place], float, list[float]]:
    """
    GA with:
      - OX1 crossover
      - Swap mutation
      - Elitism (keep best solution across all generations)
      - Stagnation early stop
    Returns (best_route, best_distance, convergence_curve).
    convergence_curve[g] = best distance found up to generation g.
    """
    random.seed(seed)

    def fitness(route):
        d = route_distance(route)
        return 1 / d if d > 0 else float("inf")

    def tournament_select(pop):
        return max(random.sample(pop, min(3, len(pop))), key=fitness)

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
        if random.random() < mutation_rate:
            i, j = random.sample(range(len(route)), 2)
            route[i], route[j] = route[j], route[i]
        return route

    population = [random.sample(places, len(places)) for _ in range(pop_size)]

    best_ever = max(population, key=fitness)
    best_ever_dist = route_distance(best_ever)
    stagnation = 0
    convergence = []

    for _ in range(generations):
        best_gen = max(population, key=fitness)
        best_gen_dist = route_distance(best_gen)

        if best_gen_dist < best_ever_dist:
            best_ever = best_gen[:]
            best_ever_dist = best_gen_dist
            stagnation = 0
        else:
            stagnation += 1
            if stagnation >= stagnation_limit:
                # Pad convergence curve to full length
                if record_convergence:
                    remaining = generations - len(convergence)
                    convergence.extend([best_ever_dist] * remaining)
                break

        if record_convergence:
            convergence.append(best_ever_dist)

        new_pop = [best_ever[:]]  # elitism
        while len(new_pop) < pop_size:
            child = ox1_crossover(tournament_select(population), tournament_select(population))
            child = swap_mutate(child)
            new_pop.append(child)
        population = new_pop

    if record_convergence and len(convergence) < generations:
        convergence.extend([best_ever_dist] * (generations - len(convergence)))

    return best_ever, best_ever_dist, convergence


# ── Test case builder ─────────────────────────────────────────────────────────
def load_test_places(province: Optional[str] = None, n: int = 6) -> list[Place]:
    """
    Load n places with valid Cambodia coordinates from cleaned data.
    If province is None, sample from all provinces.
    """
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Data file not found: {DATA_FILE}\n"
            "Run the pipeline first (merge → clean → train)."
        )

    df = pd.read_csv(DATA_FILE)

    # Parse coordinates from position column
    lats, lngs = [], []
    for pos in df.get("position", pd.Series()):
        try:
            d = ast.literal_eval(str(pos))
            lats.append(float(d.get("lat", float("nan"))))
            lngs.append(float(d.get("lng", float("nan"))))
        except Exception:
            lats.append(float("nan"))
            lngs.append(float("nan"))

    df["_lat"] = lats
    df["_lng"] = lngs

    # Cambodia bounding box filter
    mask = (
        df["_lat"].between(9.0, 15.5) &
        df["_lng"].between(102.0, 108.0)
    )
    df = df[mask].copy()

    if province:
        df = df[df["province"].str.strip().str.title() == province.strip().title()]

    if len(df) < n:
        raise ValueError(
            f"Not enough places with coordinates in province='{province}'. "
            f"Found {len(df)}, need {n}."
        )

    sample = df.sample(n, random_state=42)
    return [
        Place(
            title=str(row["title"]),
            lat=float(row["_lat"]),
            lng=float(row["_lng"]),
            province=str(row.get("province", "")),
            category=str(row.get("ontologyId", "")),
        )
        for _, row in sample.iterrows()
    ]


# ── Import ast for coordinate parsing ────────────────────────────────────────
import ast


# ── Benchmark runner ──────────────────────────────────────────────────────────
def run_benchmark(
    places: list[Place],
    trials: int = 30,
    verbose: bool = True,
) -> dict:
    """
    Run all algorithms for `trials` different seeds.
    Returns a results dict with distances, times, and convergence data.
    """
    algorithms = {
        "Random":   algo_random,
        "Greedy NN": algo_greedy_nn,
        "2-opt":    algo_2opt,
        "GA":       algo_ga,
    }

    results = {name: {"distances": [], "times_ms": []} for name in algorithms}
    all_convergences = []  # list of convergence curves (one per trial)

    for trial in range(trials):
        seed = trial * 7 + 13  # reproducible but varied seeds

        for name, algo in algorithms.items():
            t0 = time.perf_counter()
            _, dist, convergence = algo(places, seed)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            results[name]["distances"].append(dist)
            results[name]["times_ms"].append(elapsed_ms)

            if name == "GA" and convergence:
                all_convergences.append(convergence)

    results["GA"]["convergence_mean"] = (
        np.mean(all_convergences, axis=0).tolist() if all_convergences else []
    )

    if verbose:
        _print_results(results, places, trials)

    return results


def _print_results(results: dict, places: list[Place], trials: int) -> None:
    n = len(places)
    province = places[0].province if places else "unknown"

    print(f"\n{'='*65}")
    print(f"  GA Benchmark  |  province={province}  n={n}  trials={trials}")
    print(f"{'='*65}")
    print(f"  {'Algorithm':<14}  {'Mean dist (km)':>14}  {'Std':>8}  {'Mean time':>10}")
    print(f"  {'-'*56}")

    best_mean = min(np.mean(v["distances"]) for v in results.values())

    for name, data in results.items():
        mean_d = np.mean(data["distances"])
        std_d = np.std(data["distances"])
        mean_t = np.mean(data["times_ms"])
        marker = " ◀ best" if abs(mean_d - best_mean) < 1e-6 else ""
        print(f"  {name:<14}  {mean_d:>14.2f}  {std_d:>8.2f}  {mean_t:>8.1f}ms{marker}")

    # Wilcoxon: GA vs 2-opt (strongest deterministic baseline)
    if HAS_SCIPY:
        ga_dists = results["GA"]["distances"]
        opt_dists = results["2-opt"]["distances"]
        try:
            stat, p = wilcoxon(ga_dists, opt_dists)
            print(f"\n  Wilcoxon (GA vs 2-opt): stat={stat:.3f}, p={p:.4f}", end="")
            if p < 0.05:
                better = "GA" if np.mean(ga_dists) < np.mean(opt_dists) else "2-opt"
                print(f"  → {better} is significantly better (α=0.05)")
            else:
                print("  → no significant difference (α=0.05)")
        except Exception as e:
            print(f"\n  Wilcoxon test skipped: {e}")

    # GA improvement over random (how much value the GA adds)
    random_mean = np.mean(results["Random"]["distances"])
    ga_mean = np.mean(results["GA"]["distances"])
    improvement = (random_mean - ga_mean) / random_mean * 100
    print(f"\n  GA improvement over random: {improvement:.1f}%")
    print(f"{'='*65}\n")


def save_convergence_csv(results: dict, output_path: Path) -> None:
    """Save GA convergence curve to CSV for plotting."""
    curve = results["GA"].get("convergence_mean", [])
    if not curve:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "generation": range(len(curve)),
        "best_distance_km": curve,
    }).to_csv(output_path, index=False)
    print(f"Convergence data saved → {output_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Benchmark GA routing algorithms")
    parser.add_argument("--province", default=None, help="Province to sample places from")
    parser.add_argument("--n", type=int, default=6, help="Number of places per test case (default: 6)")
    parser.add_argument("--trials", type=int, default=30, help="Random trials per algorithm (default: 30)")
    parser.add_argument("--save", action="store_true", help="Save convergence CSV to benchmarks/results/")
    args = parser.parse_args()

    print(f"Loading {args.n} places" + (f" from {args.province}" if args.province else " (all provinces)") + "...")
    places = load_test_places(province=args.province, n=args.n)
    print(f"Loaded: {[p.title for p in places]}\n")

    results = run_benchmark(places, trials=args.trials)

    if args.save:
        province_slug = (args.province or "all").replace(" ", "_").lower()
        out = RESULTS_DIR / f"convergence_{province_slug}_n{args.n}.csv"
        save_convergence_csv(results, out)

    # Run across multiple problem sizes to show scaling behaviour
    print("\n--- Scaling test (n = 4, 6, 8) ---")
    for n in [4, 6, 8]:
        try:
            p = load_test_places(province=args.province, n=n)
            run_benchmark(p, trials=args.trials, verbose=True)
        except ValueError as e:
            print(f"  n={n}: skipped ({e})")


if __name__ == "__main__":
    main()
