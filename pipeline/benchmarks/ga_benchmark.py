"""
GA Benchmark: Compare routing algorithms on the Sak Tmor trip planning problem.

Algorithms compared:
  1. Random         — random permutation (lower bound baseline)
  2. Greedy NN      — nearest-neighbor heuristic (fast practical baseline)
  3. 2-opt          — local search only (strong deterministic baseline)
  4. GA (basic)     — OX1 crossover + swap mutation + elitism (Week 1)
  5. GA (memetic)   — GA + 2-opt per child + adaptive mutation + bandit operators (Week 2)

Metrics (over 30 trials per test case):
  - Route distance (km): mean ± std
  - Computation time (ms): mean ± std
  - For GA variants: convergence curve (best distance per generation, averaged over trials)

Statistical tests:
  - Wilcoxon signed-rank: memetic vs basic GA, and memetic vs 2-opt

Usage:
  python pipeline/benchmarks/ga_benchmark.py
  python pipeline/benchmarks/ga_benchmark.py --province "Siem Reap" --n 6 --trials 50 --save
"""

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

BACKEND_SITE_PACKAGES = Path(__file__).parent.parent.parent / "backend" / "venv" / "Lib" / "site-packages"
if BACKEND_SITE_PACKAGES.exists() and str(BACKEND_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(BACKEND_SITE_PACKAGES))

try:
    from scipy.stats import wilcoxon
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[warn] scipy not installed — Wilcoxon test will be skipped. pip install scipy")

# ── Data paths ────────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent.parent.parent / "backend" / "data" / "cleaned_merged_data.csv"
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


# ── Algorithm 5: GA Memetic (mirrors api.py _optimize_route exactly) ──────────
def algo_ga_memetic(
    places: list[Place],
    seed: int,
    pop_size: int = 30,
    generations: int = 50,
    stagnation_limit: int = 15,
    two_opt_iters: int = 3,
    record_convergence: bool = True,
) -> tuple[list[Place], float, list[float]]:
    """
    Week 2 Memetic GA:
      - OX1 crossover (same as basic)
      - 2-opt local search applied to every child (memetic step)
      - Adaptive mutation rate: CV-based, ramps 0.1–0.5 with population diversity
      - Multi-operator bandit: ε-greedy selection over swap / inversion / insertion
      - Elitism + stagnation early stop
    Returns (best_route, best_distance, convergence_curve).
    """
    random.seed(seed)
    np.random.seed(seed)
    EPSILON = 0.1  # bandit exploration rate

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

    # ── Memetic: 2-opt local search ───────────────────────────────────────────
    def two_opt_local(route):
        best = route[:]
        best_dist = route_distance(best)
        for _ in range(two_opt_iters):
            improved = False
            for i in range(1, len(best) - 1):
                for j in range(i + 1, len(best)):
                    candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                    cand_dist = route_distance(candidate)
                    if cand_dist < best_dist - 1e-10:
                        best = candidate
                        best_dist = cand_dist
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break
        return best

    # ── Adaptive mutation rate (CV-based) ─────────────────────────────────────
    def get_mutation_rate(population):
        fitnesses = [fitness(r) for r in population]
        mean_fit = float(np.mean(fitnesses))
        std_fit = float(np.std(fitnesses))
        if mean_fit > 0:
            cv = std_fit / mean_fit
            return 0.1 + 0.4 * cv  # ramps 0.1 (converged) → 0.5 (diverse)
        return 0.3

    # ── Multi-operator bandit ─────────────────────────────────────────────────
    ops_trials   = {"swap": 0, "inversion": 0, "insertion": 0}
    ops_successes = {"swap": 0, "inversion": 0, "insertion": 0}

    def bandit_select():
        if random.random() < EPSILON:
            return random.choice(list(ops_trials.keys()))
        rates = {op: ops_successes[op] / (ops_trials[op] + 1e-6) for op in ops_trials}
        return max(rates, key=rates.get)

    def bandit_update(op, improved):
        ops_trials[op] += 1
        if improved:
            ops_successes[op] += 1

    def swap_mutate(route):
        r = route[:]
        if len(r) >= 2:
            i, j = random.sample(range(len(r)), 2)
            r[i], r[j] = r[j], r[i]
        return r

    def inversion_mutate(route):
        r = route[:]
        if len(r) >= 3:
            s, e = sorted(random.sample(range(len(r)), 2))
            r[s:e + 1] = r[s:e + 1][::-1]
        return r

    def insertion_mutate(route):
        r = route[:]
        if len(r) >= 3:
            i = random.randint(0, len(r) - 1)
            place = r.pop(i)
            j = random.randint(0, len(r))
            r.insert(j, place)
        return r

    # ── Main GA loop ──────────────────────────────────────────────────────────
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
                if record_convergence:
                    convergence.extend([best_ever_dist] * (generations - len(convergence)))
                break

        if record_convergence:
            convergence.append(best_ever_dist)

        mut_rate = get_mutation_rate(population)
        new_pop = [best_ever[:]]  # elitism

        while len(new_pop) < pop_size:
            child = ox1_crossover(
                tournament_select(population),
                tournament_select(population),
            )

            # Memetic: 2-opt polish before mutation
            pre_mut_dist = route_distance(child)
            child = two_opt_local(child)
            post_2opt_dist = route_distance(child)

            # Bandit-selected mutation
            if random.random() < mut_rate:
                op = bandit_select()
                if op == "swap":
                    mutated = swap_mutate(child)
                elif op == "inversion":
                    mutated = inversion_mutate(child)
                else:
                    mutated = insertion_mutate(child)
                improved = route_distance(mutated) < post_2opt_dist
                bandit_update(op, improved)
                child = mutated

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
        "Random":      algo_random,
        "Greedy NN":   algo_greedy_nn,
        "2-opt":       algo_2opt,
        "GA (basic)":  algo_ga,
        "GA (memetic)": algo_ga_memetic,
    }

    results = {name: {"distances": [], "times_ms": []} for name in algorithms}
    ga_basic_convergences: list[list[float]] = []
    ga_memetic_convergences: list[list[float]] = []

    for trial in range(trials):
        seed = trial * 7 + 13  # reproducible but varied seeds

        for name, algo in algorithms.items():
            t0 = time.perf_counter()
            _, dist, convergence = algo(places, seed)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            results[name]["distances"].append(dist)
            results[name]["times_ms"].append(elapsed_ms)

            if name == "GA (basic)" and convergence:
                ga_basic_convergences.append(convergence)
            if name == "GA (memetic)" and convergence:
                ga_memetic_convergences.append(convergence)

    results["GA (basic)"]["convergence_mean"] = (
        np.mean(ga_basic_convergences, axis=0).tolist() if ga_basic_convergences else []
    )
    results["GA (memetic)"]["convergence_mean"] = (
        np.mean(ga_memetic_convergences, axis=0).tolist() if ga_memetic_convergences else []
    )

    if verbose:
        _print_results(results, places, trials)

    return results


def _print_results(results: dict, places: list[Place], trials: int) -> None:
    n = len(places)
    province = places[0].province if places else "unknown"

    W = 74
    print(f"\n{'='*W}")
    print(f"  GA Benchmark  |  province={province}  n={n}  trials={trials}")
    print(f"{'='*W}")
    print(f"  {'Algorithm':<16}  {'Mean (km)':>10}  {'Std':>7}  {'Min':>7}  {'Max':>7}  {'Time':>9}")
    print(f"  {'-'*(W-2)}")

    best_mean = min(np.mean(v["distances"]) for v in results.values())

    for name, data in results.items():
        dists  = data["distances"]
        mean_d = np.mean(dists)
        std_d  = np.std(dists)
        min_d  = np.min(dists)
        max_d  = np.max(dists)
        mean_t = np.mean(data["times_ms"])
        marker = " <-- best" if abs(mean_d - best_mean) < 1e-6 else ""
        print(
            f"  {name:<16}  {mean_d:>10.2f}  {std_d:>7.2f}"
            f"  {min_d:>7.2f}  {max_d:>7.2f}  {mean_t:>7.1f}ms{marker}"
        )

    print(f"  {'-'*(W-2)}")

    # ── Improvement summary ────────────────────────────────────────────────────
    random_mean  = np.mean(results["Random"]["distances"])
    basic_mean   = np.mean(results["GA (basic)"]["distances"])
    memetic_mean = np.mean(results["GA (memetic)"]["distances"])
    opt_mean     = np.mean(results["2-opt"]["distances"])

    def pct(base, improved):
        return (base - improved) / base * 100 if base > 0 else 0.0

    print(f"\n  Improvement over random baseline:")
    print(f"    GA (basic)   : {pct(random_mean, basic_mean):+.1f}%")
    print(f"    GA (memetic) : {pct(random_mean, memetic_mean):+.1f}%")
    print(f"  Memetic vs 2-opt   : {pct(opt_mean, memetic_mean):+.1f}%")
    print(f"  Memetic vs GA basic: {pct(basic_mean, memetic_mean):+.1f}%")

    # ── Wilcoxon signed-rank tests ─────────────────────────────────────────────
    if HAS_SCIPY:
        pairs = [
            ("GA (memetic)", "GA (basic)", "memetic vs basic"),
            ("GA (memetic)", "2-opt",      "memetic vs 2-opt"),
            ("GA (basic)",  "2-opt",       "basic   vs 2-opt"),
        ]
        print(f"\n  Wilcoxon signed-rank tests (a=0.05):")
        for a_name, b_name, label in pairs:
            a = results[a_name]["distances"]
            b = results[b_name]["distances"]
            try:
                if np.allclose(a, b):
                    p = 1.0
                    stat = 0.0
                else:
                    stat, p = wilcoxon(a, b)
                sig    = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
                better = a_name if np.mean(a) < np.mean(b) else b_name
                print(f"    {label:<24}  p={p:.4f}  {sig:<4}  -> {better} wins")
            except Exception as e:
                print(f"    {label:<24}  skipped ({e})")

    print(f"\n  Note: GA (memetic) uses e-greedy bandit (e=0.1) over")
    print(f"        swap / inversion / insertion mutation operators.")
    print(f"{'='*W}\n")


def save_convergence_csv(results: dict, output_path: Path) -> None:
    """
    Save convergence curves for both GA (basic) and GA (memetic) to one CSV.
    Columns: generation, ga_basic_km, ga_memetic_km
    Also writes individual files alongside the combined one.
    """
    basic_curve   = results["GA (basic)"].get("convergence_mean", [])
    memetic_curve = results["GA (memetic)"].get("convergence_mean", [])

    if not basic_curve and not memetic_curve:
        print("[warn] No convergence data to save.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    max_len = max(len(basic_curve), len(memetic_curve))

    # Pad shorter curve to same length
    basic_padded   = basic_curve   + [basic_curve[-1]]   * (max_len - len(basic_curve))   if basic_curve   else [None] * max_len
    memetic_padded = memetic_curve + [memetic_curve[-1]] * (max_len - len(memetic_curve)) if memetic_curve else [None] * max_len

    combined_path = output_path
    pd.DataFrame({
        "generation":      range(max_len),
        "ga_basic_km":     basic_padded,
        "ga_memetic_km":   memetic_padded,
    }).to_csv(combined_path, index=False)
    print(f"Combined convergence saved -> {combined_path}")

    # Individual files for separate plotting
    stem = output_path.stem
    if basic_curve:
        p = output_path.with_name(stem + "_basic.csv")
        pd.DataFrame({"generation": range(len(basic_curve)), "best_distance_km": basic_curve}).to_csv(p, index=False)
        print(f"  GA (basic)   -> {p}")
    if memetic_curve:
        p = output_path.with_name(stem + "_memetic.csv")
        pd.DataFrame({"generation": range(len(memetic_curve)), "best_distance_km": memetic_curve}).to_csv(p, index=False)
        print(f"  GA (memetic) -> {p}")


def build_summary(results: dict, places: list[Place], trials: int) -> dict:
    """Build a report-friendly summary of benchmark results."""
    province = places[0].province if places else "unknown"
    n = len(places)

    algorithms = {}
    for name, data in results.items():
        distances = data["distances"]
        times_ms = data["times_ms"]
        algorithms[name] = {
            "mean_km": round(float(np.mean(distances)), 4),
            "std_km": round(float(np.std(distances)), 4),
            "min_km": round(float(np.min(distances)), 4),
            "max_km": round(float(np.max(distances)), 4),
            "mean_time_ms": round(float(np.mean(times_ms)), 4),
            "std_time_ms": round(float(np.std(times_ms)), 4),
        }

    def pct(base_name: str, improved_name: str) -> float:
        base = algorithms[base_name]["mean_km"]
        improved = algorithms[improved_name]["mean_km"]
        return round(((base - improved) / base * 100) if base > 0 else 0.0, 4)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "province": province,
        "n_places": n,
        "trials": trials,
        "algorithms": algorithms,
        "improvements_pct": {
            "ga_basic_over_random": pct("Random", "GA (basic)"),
            "ga_memetic_over_random": pct("Random", "GA (memetic)"),
            "ga_memetic_over_2opt": pct("2-opt", "GA (memetic)"),
            "ga_memetic_over_ga_basic": pct("GA (basic)", "GA (memetic)"),
        },
        "wilcoxon": [],
        "report_ready_claims": [],
        "analysis_notes": [],
    }

    if HAS_SCIPY:
        pairs = [
            ("GA (memetic)", "GA (basic)", "memetic_vs_basic"),
            ("GA (memetic)", "2-opt", "memetic_vs_2opt"),
            ("GA (basic)", "2-opt", "basic_vs_2opt"),
        ]
        for a_name, b_name, label in pairs:
            a = results[a_name]["distances"]
            b = results[b_name]["distances"]
            if np.allclose(a, b):
                stat = 0.0
                p = 1.0
            else:
                stat, p = wilcoxon(a, b)
            better = a_name if np.mean(a) < np.mean(b) else b_name
            summary["wilcoxon"].append({
                "comparison": label,
                "a": a_name,
                "b": b_name,
                "statistic": round(float(stat), 4),
                "p_value": round(float(p), 6),
                "winner": better,
            })

    memetic_std = algorithms["GA (memetic)"]["std_km"]
    if memetic_std < 0.01:
        summary["analysis_notes"].append(
            "GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating."
        )
    if summary["improvements_pct"]["ga_memetic_over_2opt"] > 0:
        summary["analysis_notes"].append(
            "Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone."
        )
    if algorithms["GA (memetic)"]["mean_time_ms"] < 50:
        summary["analysis_notes"].append(
            "Mean memetic GA runtime stayed below 50 ms for this problem size, which is suitable for interactive trip generation."
        )

    memetic_vs_2opt = next((w for w in summary["wilcoxon"] if w["comparison"] == "memetic_vs_2opt"), None)
    if memetic_vs_2opt and memetic_vs_2opt["winner"] == "GA (memetic)":
        summary["report_ready_claims"].append(
            (
                f"For {province} benchmark cases with n={n} places over {trials} trials, "
                f"the memetic GA achieved {summary['improvements_pct']['ga_memetic_over_2opt']:.2f}% "
                f"shorter routes than deterministic 2-opt (Wilcoxon p={memetic_vs_2opt['p_value']:.6f})."
            )
        )

    memetic_vs_basic = next((w for w in summary["wilcoxon"] if w["comparison"] == "memetic_vs_basic"), None)
    if memetic_vs_basic and memetic_vs_basic["winner"] == "GA (memetic)":
        summary["report_ready_claims"].append(
            (
                f"Against the Week 1 baseline GA, the Week 2 memetic GA improved mean route length by "
                f"{summary['improvements_pct']['ga_memetic_over_ga_basic']:.2f}% for {province} n={n} cases."
            )
        )

    return summary


def render_summary_markdown(summary: dict) -> str:
    """Render a compact Markdown benchmark note for the thesis/report log."""
    lines = [
        f"# Benchmark Summary: {summary['province']} n={summary['n_places']}",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Trials: {summary['trials']}",
        "",
        "## Algorithm Metrics",
        "",
        "| Algorithm | Mean km | Std km | Mean time (ms) |",
        "|---|---:|---:|---:|",
    ]

    for name, stats in summary["algorithms"].items():
        lines.append(
            f"| {name} | {stats['mean_km']:.2f} | {stats['std_km']:.2f} | {stats['mean_time_ms']:.2f} |"
        )

    lines.extend([
        "",
        "## Improvements",
        "",
        f"- GA (basic) vs Random: {summary['improvements_pct']['ga_basic_over_random']:.2f}%",
        f"- GA (memetic) vs Random: {summary['improvements_pct']['ga_memetic_over_random']:.2f}%",
        f"- GA (memetic) vs 2-opt: {summary['improvements_pct']['ga_memetic_over_2opt']:.2f}%",
        f"- GA (memetic) vs GA (basic): {summary['improvements_pct']['ga_memetic_over_ga_basic']:.2f}%",
        "",
        "## Statistical Tests",
        "",
    ])

    if summary["wilcoxon"]:
        for test in summary["wilcoxon"]:
            lines.append(
                f"- `{test['comparison']}`: p={test['p_value']:.6f}, winner={test['winner']}"
            )
    else:
        lines.append("- Wilcoxon tests not available in this environment.")

    lines.extend([
        "",
        "## Analysis Notes",
        "",
    ])
    if summary["analysis_notes"]:
        for note in summary["analysis_notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- No additional analysis notes generated automatically.")

    lines.extend([
        "",
        "## Report-Ready Claims",
        "",
    ])
    if summary["report_ready_claims"]:
        for claim in summary["report_ready_claims"]:
            lines.append(f"- {claim}")
    else:
        lines.append("- No statistically backed claim generated automatically.")

    lines.append("")
    return "\n".join(lines)


def save_summary_artifacts(results: dict, output_path: Path, places: list[Place], trials: int) -> None:
    """Save machine-readable and report-ready benchmark summaries beside the CSV files."""
    summary = build_summary(results, places, trials)
    stem = output_path.stem

    json_path = output_path.with_name(stem + "_summary.json")
    md_path = output_path.with_name(stem + "_summary.md")

    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(render_summary_markdown(summary), encoding="utf-8")

    print(f"Summary JSON saved -> {json_path}")
    print(f"Summary Markdown saved -> {md_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Benchmark GA routing algorithms")
    parser.add_argument("--province", default=None, help="Province to sample places from (default: all)")
    parser.add_argument("--n",      type=int, default=6,  help="Places per test case (default: 6)")
    parser.add_argument("--trials", type=int, default=30, help="Trials per algorithm (default: 30)")
    parser.add_argument("--save",   action="store_true",  help="Save convergence CSVs to benchmarks/results/")
    parser.add_argument("--no-scale", action="store_true", help="Skip the n=4/6/8 scaling test")
    args = parser.parse_args()

    province_label = args.province or "(all provinces)"
    print(f"Loading {args.n} places from {province_label} ...")
    places = load_test_places(province=args.province, n=args.n)
    print(f"Loaded: {[p.title for p in places]}\n")

    results = run_benchmark(places, trials=args.trials)

    if args.save:
        province_slug = (args.province or "all").replace(" ", "_").lower()
        out = RESULTS_DIR / f"convergence_{province_slug}_n{args.n}.csv"
        save_convergence_csv(results, out)
        save_summary_artifacts(results, out, places, args.trials)

    # Scaling test: show how each algorithm scales with problem size
    if not args.no_scale:
        sizes = [n for n in [4, 6, 8] if n != args.n]
        if sizes:
            print("\n--- Scaling test (n = " + ", ".join(map(str, sizes)) + ") ---")
            for n in sizes:
                try:
                    p = load_test_places(province=args.province, n=n)
                    sub = run_benchmark(p, trials=args.trials, verbose=True)
                    if args.save:
                        province_slug = (args.province or "all").replace(" ", "_").lower()
                        out = RESULTS_DIR / f"convergence_{province_slug}_n{n}.csv"
                        save_convergence_csv(sub, out)
                        save_summary_artifacts(sub, out, p, args.trials)
                except ValueError as e:
                    print(f"  n={n}: skipped ({e})")


if __name__ == "__main__":
    main()
