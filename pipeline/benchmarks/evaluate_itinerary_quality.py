"""
Offline itinerary-quality evaluation for Week 5.

Metrics:
  - diversity_entropy: normalized Shannon entropy of activity categories
  - spatial_efficiency_km_per_activity: total route km per activity
  - score_density: mean weighted recommendation score of returned activities
  - hidden_gem_rate: fraction of returned activities marked as hidden gems
  - coverage: unique recommended activity IDs / unique candidate activity IDs
"""

import argparse
import math
import random
from collections import Counter
from pathlib import Path

import numpy as np

from benchmark_utils import (
    ID_LOOKUP,
    calculate_weighted_score,
    candidate_activity_ids,
    ensure_results_dir,
    flatten_activities,
    generate_trip,
    random_request,
    save_json,
    save_markdown,
    summarize_series,
    timestamp,
)


def normalized_entropy(labels: list[str]) -> float:
    if not labels:
        return 0.0
    counts = Counter(labels)
    probs = [count / len(labels) for count in counts.values()]
    entropy = -sum(p * math.log(p) for p in probs if p > 0)
    if len(counts) <= 1:
        return 0.0
    return entropy / math.log(len(counts))


def activity_score_density(activity_ids: list[str]) -> float:
    scores = []
    for place_id in activity_ids:
        if place_id in ID_LOOKUP.index:
            row = ID_LOOKUP.loc[place_id]
            scores.append(calculate_weighted_score(row))
    return float(np.mean(scores)) if scores else 0.0


def evaluate_requests(base_url: str, requests: list[dict]) -> dict:
    trip_metrics = []
    recommended_ids = set()
    candidate_ids = set()

    for req in requests:
        response = generate_trip(base_url, req)
        activities = flatten_activities(response)
        activity_ids = [place["id"] for place in activities]
        categories = [place["category"] for place in activities]
        total_distance = sum(day["distance_km"] for day in response["itinerary"])
        activity_count = max(1, len(activity_ids))

        recommended_ids.update(activity_ids)
        candidate_ids.update(candidate_activity_ids(req))

        trip_metrics.append({
            "province": req["province"],
            "days": req["days"],
            "mode": req["mode"],
            "activity_count": activity_count,
            "total_distance_km": round(total_distance, 4),
            "diversity_entropy": round(normalized_entropy(categories), 4),
            "spatial_efficiency_km_per_activity": round(total_distance / activity_count, 4),
            "score_density": round(activity_score_density(activity_ids), 4),
            "hidden_gem_rate": round(
                sum(1 for place in activities if place.get("is_hidden_gem")) / activity_count, 4
            ),
        })

    summary = {
        "generated_at": timestamp(),
        "trip_count": len(requests),
        "coverage": round(len(recommended_ids) / len(candidate_ids), 4) if candidate_ids else 0.0,
        "metrics": {
            "diversity_entropy": summarize_series(m["diversity_entropy"] for m in trip_metrics),
            "spatial_efficiency_km_per_activity": summarize_series(
                m["spatial_efficiency_km_per_activity"] for m in trip_metrics
            ),
            "score_density": summarize_series(m["score_density"] for m in trip_metrics),
            "hidden_gem_rate": summarize_series(m["hidden_gem_rate"] for m in trip_metrics),
            "total_distance_km": summarize_series(m["total_distance_km"] for m in trip_metrics),
        },
        "sample_requests": [
            {
                "province": req["province"],
                "days": req["days"],
                "activities": req["activities"],
                "accommodation": req["accommodation"],
                "dining": req["dining"],
                "perDay": req["perDay"],
                "mode": req["mode"],
            }
            for req in requests[:3]
        ],
        "analysis_notes": [],
    }

    if summary["metrics"]["hidden_gem_rate"]["mean"] == 0.0:
        summary["analysis_notes"].append(
            "Hidden-gem rate is zero for this sample; inspect whether the metric is too strict or the sampled requests are biased toward mainstream categories."
        )
    if summary["coverage"] < 0.2:
        summary["analysis_notes"].append(
            "Coverage is low relative to the candidate pool, which may indicate over-concentration on a small set of highly scored places."
        )
    if summary["metrics"]["diversity_entropy"]["mean"] < 0.5:
        summary["analysis_notes"].append(
            "Category diversity is moderate to low in this sample, suggesting room to tune exploration or diversity-aware sampling."
        )

    return {
        "summary": summary,
        "trips": trip_metrics,
    }


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    metrics = summary["metrics"]
    lines = [
        "# Itinerary Quality Evaluation",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Trips evaluated: {summary['trip_count']}",
        f"- Coverage: {summary['coverage']:.2%}",
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Mean | Std | Min | Max |",
        "|---|---:|---:|---:|---:|",
    ]

    for name, values in metrics.items():
        lines.append(
            f"| {name} | {values['mean']:.4f} | {values['std']:.4f} | {values['min']:.4f} | {values['max']:.4f} |"
        )

    lines.extend([
        "",
        "## Analysis Notes",
        "",
    ])
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
    for req in summary["sample_requests"]:
        lines.append(
            f"- `{req['province']}` | {req['days']} days | mode=`{req['mode']}` | activities={req['activities']}"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate offline itinerary-quality metrics")
    parser.add_argument("--province", default=None, help="Province to lock requests to")
    parser.add_argument("--trips", type=int, default=30, help="Number of random trip requests")
    parser.add_argument("--days", type=int, default=3, help="Trip length in days")
    parser.add_argument("--per-day", type=int, default=3, dest="per_day", help="Activities per day")
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
        for _ in range(args.trips)
    ]
    report = evaluate_requests(args.base_url, requests)

    print(render_markdown(report))

    if args.save:
        out_dir = ensure_results_dir()
        province_slug = (args.province or "mixed").replace(" ", "_").lower()
        stem = f"itinerary_quality_{province_slug}_{args.mode}_{args.trips}trips"
        json_path = out_dir / f"{stem}.json"
        md_path = out_dir / f"{stem}.md"
        save_json(json_path, report)
        save_markdown(md_path, render_markdown(report))
        print(f"Saved JSON -> {json_path}")
        print(f"Saved Markdown -> {md_path}")


if __name__ == "__main__":
    main()
