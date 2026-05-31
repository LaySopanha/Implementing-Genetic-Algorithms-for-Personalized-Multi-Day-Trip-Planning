# Itinerary Quality Evaluation

- Generated: 2026-05-08T21:12:20
- Trips evaluated: 50
- Coverage: 47.62%

## Aggregate Metrics

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| diversity_entropy | 0.2601 | 0.3998 | 0.0000 | 1.0000 |
| spatial_efficiency_km_per_activity | 6.0790 | 6.9708 | 0.7000 | 35.7750 |
| score_density | 2.8287 | 0.3620 | 1.9966 | 3.6703 |
| hidden_gem_rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| total_distance_km | 24.3160 | 27.8830 | 2.8000 | 143.1000 |

## Analysis Notes

- Hidden-gem rate is zero for this sample; inspect whether the metric is too strict or the sampled requests are biased toward mainstream categories.
- Category diversity is moderate to low in this sample, suggesting room to tune exploration or diversity-aware sampling.

## Sample Requests

- `Siem Reap` | 2 days | mode=`balanced` | activities=['Waterfall', 'Art Gallery']
- `Siem Reap` | 2 days | mode=`balanced` | activities=['Historical Site', 'Wildlife / Zoo']
- `Siem Reap` | 2 days | mode=`balanced` | activities=['Waterfall', 'Park / Nature']
