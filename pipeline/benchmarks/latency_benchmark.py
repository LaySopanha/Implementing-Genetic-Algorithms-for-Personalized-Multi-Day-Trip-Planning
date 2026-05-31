"""
Latency benchmark for itinerary generation.

Measures direct backend trip-generation latency without HTTP overhead and reports:
  - p50 / p95 / p99 latency
  - mean / std latency
  - request mix used during the run
"""

import argparse
import random
import time

import numpy as np

from benchmark_utils import (
    ensure_results_dir,
    generate_trip,
    random_request,
    save_json,
    save_markdown,
    summarize_series,
    timestamp,
)


def percentile(values: list[float], q: float) -> float:
    return round(float(np.percentile(np.array(values, dtype=float), q)), 4)


def run_latency_benchmark(base_url: str, requests: list[dict]) -> dict:
    latencies_ms = []
    request_rows = []

    for req in requests:
        t0 = time.perf_counter()
        response = generate_trip(base_url, req)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies_ms.append(elapsed_ms)
        request_rows.append({
            "province": req["province"],
            "days": req["days"],
            "mode": req["mode"],
            "per_day": req["perDay"],
            "activity_count": sum(len(day["activities"]) for day in response["itinerary"]),
            "latency_ms": round(elapsed_ms, 4),
        })

    summary = {
        "generated_at": timestamp(),
        "request_count": len(requests),
        "latency_ms": {
            **summarize_series(latencies_ms),
            "p50": percentile(latencies_ms, 50),
            "p95": percentile(latencies_ms, 95),
            "p99": percentile(latencies_ms, 99),
        },
        "analysis_notes": [],
        "sample_requests": request_rows[:5],
    }

    if summary["latency_ms"]["p95"] > 2000:
        summary["analysis_notes"].append(
            "p95 latency exceeds the 2-second UX target and should be profiled before production use."
        )
    if summary["latency_ms"]["p99"] > summary["latency_ms"]["p50"] * 2:
        summary["analysis_notes"].append(
            "High tail latency relative to p50 suggests request-level variance worth profiling."
        )
    if summary["latency_ms"]["p50"] < 500:
        summary["analysis_notes"].append(
            "Median latency is comfortably interactive for local API execution."
        )

    return {
        "summary": summary,
        "requests": request_rows,
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    latency = summary["latency_ms"]
    lines = [
        "# Latency Benchmark",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Requests benchmarked: {summary['request_count']}",
        "",
        "## Latency Metrics",
        "",
        "| Metric | ms |",
        "|---|---:|",
        f"| mean | {latency['mean']:.4f} |",
        f"| std | {latency['std']:.4f} |",
        f"| min | {latency['min']:.4f} |",
        f"| max | {latency['max']:.4f} |",
        f"| p50 | {latency['p50']:.4f} |",
        f"| p95 | {latency['p95']:.4f} |",
        f"| p99 | {latency['p99']:.4f} |",
        "",
        "## Analysis Notes",
        "",
    ]

    if summary["analysis_notes"]:
        for note in summary["analysis_notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- No automatic issues flagged in this sample.")

    lines.extend([
        "",
        "## Sample Requests",
        "",
    ])
    for row in summary["sample_requests"]:
        lines.append(
            f"- `{row['province']}` | {row['days']} days | mode=`{row['mode']}` | latency={row['latency_ms']:.2f} ms"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark itinerary-generation latency")
    parser.add_argument("--province", default=None, help="Province to lock requests to")
    parser.add_argument("--requests", type=int, default=50, help="Number of requests to benchmark")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--per-day", type=int, default=3, dest="per_day")
    parser.add_argument("--mode", default="balanced", choices=["adventure", "balanced", "chill"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    requests = [
        random_request(
            rng,
            base_url=args.base_url,
            province=args.province,
            days=args.days,
            per_day=args.per_day,
            mode=args.mode,
        )
        for _ in range(args.requests)
    ]
    report = run_latency_benchmark(args.base_url, requests)

    print(render_markdown(report))

    if args.save:
        out_dir = ensure_results_dir()
        province_slug = (args.province or "mixed").replace(" ", "_").lower()
        stem = f"latency_{province_slug}_{args.mode}_{args.requests}req"
        json_path = out_dir / f"{stem}.json"
        md_path = out_dir / f"{stem}.md"
        save_json(json_path, report)
        save_markdown(md_path, render_markdown(report))
        print(f"Saved JSON -> {json_path}")
        print(f"Saved Markdown -> {md_path}")


if __name__ == "__main__":
    main()
