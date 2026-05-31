# Sak Tmor Experiment Log

This file is the report-writing companion for benchmarks, discoveries, and analysis.

## How To Use

1. Run a benchmark with saved artifacts:
   `python pipeline/benchmarks/ga_benchmark.py --province "Siem Reap" --n 6 --trials 30 --save`
2. Copy the key findings from the generated `*_summary.md` file in `pipeline/benchmarks/results/`.
3. Add one entry below for each benchmark, discovery, or analysis step.
4. Only promote a sentence into the thesis when it is backed by an artifact path.

## Entry Template

### [Date] Short Title
- Type: `benchmark` | `discovery` | `analysis`
- Goal:
- Method:
- Artifacts:
- Key findings:
- Report-ready claim:
- Caveats / follow-up:

## Logged Entries

### 2026-05-08 Week 2 GA Benchmark Summary
- Type: `benchmark`
- Goal: Verify whether the Week 2 memetic GA improves route quality over deterministic baselines and the Week 1 GA.
- Method: `pipeline/benchmarks/ga_benchmark.py` run on Siem Reap benchmark cases with problem sizes `n=4`, `n=6`, and `n=8`, comparing Random, Greedy NN, 2-opt, GA (basic), and GA (memetic).
- Artifacts:
  `pipeline/benchmarks/results/convergence_siem_reap_n4.csv`
  `pipeline/benchmarks/results/convergence_siem_reap_n6.csv`
  `pipeline/benchmarks/results/convergence_siem_reap_n8.csv`
- Key findings:
  GA (memetic) beat deterministic 2-opt at all tested sizes.
  Improvement over 2-opt was about `7.9%` at `n=4`, `13.7%` at `n=6`, and `13.7%` at `n=8`.
  Reported Wilcoxon p-values were all below `0.001`, supporting statistical significance.
  Mean runtime stayed under `50 ms`, so the optimization remained practical for interactive trip generation.
- Report-ready claim:
  Week 2 memetic GA achieved statistically significant route-length improvements over deterministic 2-opt, with the strongest gains appearing at medium route sizes (`n=6` to `n=8`).
- Caveats / follow-up:
  The observed near-zero standard deviation for some GA runs should be checked for deterministic seeding effects before making strong stability claims.

### 2026-05-08 Week 4 Status Review
- Type: `analysis`
- Goal: Confirm whether Week 4 is fully complete before moving to Week 5 evaluation work.
- Method: Reviewed itinerary construction in `backend/api.py` and current status notes in `THESIS_REPORT.md`.
- Artifacts:
  `backend/api.py`
  `THESIS_REPORT.md`
- Key findings:
  Day-level VRPTW penalties are implemented and opening hours are parsed into place metadata.
  The system still optimizes each day separately after geographic clustering rather than encoding the whole trip as one chromosome.
  No NSGA-II, Pareto front, or user-facing multi-objective slider implementation was found.
- Report-ready claim:
  Week 4 is partially complete: time-window-aware routing is implemented, while cross-day global optimization and NSGA-II remain deferred.
- Caveats / follow-up:
  The current VRPTW implementation is simplified because it assumes a fixed start time and fixed visit duration.

### 2026-05-08 Hidden Gem Metric Wiring Fix
- Type: `discovery`
- Goal: Verify that Week 5 hidden-gem evaluation can be measured from actual itinerary outputs.
- Method: Traced hidden-gem scoring through `backend/api.py` from `_hidden_gem_score()` into `PlaceInfo` serialization.
- Artifacts:
  `backend/api.py`
- Key findings:
  Hidden-gem scoring logic already existed, but the formatted API response was not populating `is_hidden_gem` or `local_favored_score`.
  This would have made any hidden-gem-rate benchmark appear artificially low or zero even when the scorer was working.
- Report-ready claim:
  Before Week 5 evaluation, hidden-gem metadata was wired into the API response to ensure authenticity metrics reflect actual recommendation outputs.
- Caveats / follow-up:
  The metric is now measurable, but the threshold and signal weighting still need empirical evaluation.

### 2026-05-08 Week 5 Quality Benchmark Smoke Test
- Type: `benchmark`
- Goal: Establish a first offline quality baseline for diversity, spatial efficiency, score density, hidden-gem rate, and coverage.
- Method: Ran `pipeline/benchmarks/evaluate_itinerary_quality.py` against the live local API for `3` random Siem Reap requests, `2` days each, `2` activities per day, `balanced` mode.
- Artifacts:
  `pipeline/benchmarks/results/itinerary_quality_siem_reap_balanced_3trips.json`
  `pipeline/benchmarks/results/itinerary_quality_siem_reap_balanced_3trips.md`
- Key findings:
  Mean normalized diversity entropy was `0.8563`, suggesting fairly varied category mixes in this small sample.
  Mean spatial efficiency was `2.7917 km/activity`, but trip-level variance was high.
  Coverage reached `44.00%` of the locally constructed candidate set for the sampled requests.
  Hidden-gem rate was `0.0000` in this sample.
- Report-ready claim:
  Initial Week 5 quality evaluation shows good category diversity and moderate candidate coverage, but no hidden-gem yield on the sampled Siem Reap balanced itineraries.
- Caveats / follow-up:
  This was only a smoke test with `3` trips, so it should not be used for final thesis claims without scaling up the sample size.

### 2026-05-08 Week 5 Latency Benchmark Smoke Test
- Type: `benchmark`
- Goal: Establish the first p50/p95/p99 latency baseline for live itinerary generation.
- Method: Ran `pipeline/benchmarks/latency_benchmark.py` against the live local API for `5` random Siem Reap requests, `2` days each, `2` activities per day, `balanced` mode.
- Artifacts:
  `pipeline/benchmarks/results/latency_siem_reap_balanced_5req.json`
  `pipeline/benchmarks/results/latency_siem_reap_balanced_5req.md`
- Key findings:
  Median latency (`p50`) was `913.33 ms`, which is interactive.
  Tail latency was poor, with `p95 = 5042.48 ms` and `p99 = 5730.18 ms`.
  Individual requests ranged from `616.08 ms` up to `5902.10 ms`, showing substantial variance.
- Report-ready claim:
  Local trip generation appears interactive at the median but currently suffers from unstable tail latency, making performance optimization a valid Week 5 focus.
- Caveats / follow-up:
  The sample size was intentionally small for smoke testing; repeat with at least `50` requests before using these latency numbers as formal evidence.
