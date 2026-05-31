# Benchmark Artifacts

Each saved benchmark run should leave three artifact types in this folder:

- `convergence_<province>_n<size>.csv`
  Combined convergence curve for `GA (basic)` and `GA (memetic)`.
- `convergence_<province>_n<size>_summary.json`
  Machine-readable summary with mean/std metrics, improvements, and Wilcoxon results.
- `convergence_<province>_n<size>_summary.md`
  Report-ready Markdown note with benchmark interpretation.

## Suggested Workflow

1. Run:
   `python pipeline/benchmarks/ga_benchmark.py --province "Siem Reap" --n 6 --trials 30 --save`
2. Keep the CSV and JSON files as raw evidence.
3. Copy the best lines from the generated Markdown summary into `research/EXPERIMENT_LOG.md`.
4. When writing the thesis, only use claims that point back to one of these saved artifacts.

## Week 5 Scripts

- `evaluate_itinerary_quality.py`
  Calls the live local API and computes offline quality metrics from returned itineraries.
- `latency_benchmark.py`
  Calls the live local API and records p50/p95/p99 latency.

These two scripts expect the backend API to be running locally, usually at `http://127.0.0.1:8000`.
