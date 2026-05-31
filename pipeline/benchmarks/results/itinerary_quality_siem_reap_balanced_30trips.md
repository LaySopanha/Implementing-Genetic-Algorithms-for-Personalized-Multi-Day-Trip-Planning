# Itinerary Quality Evaluation

- Generated: 2026-05-08T21:11:17
- Trips evaluated: 30
- Coverage: 32.60%

## Aggregate Metrics

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| diversity_entropy | 0.2064 | 0.3764 | 0.0000 | 1.0000 |
| spatial_efficiency_km_per_activity | 7.4708 | 8.5746 | 0.9250 | 39.2000 |
| score_density | 2.8590 | 0.3293 | 2.1610 | 3.5810 |
| hidden_gem_rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| total_distance_km | 29.8833 | 34.2985 | 3.7000 | 156.8000 |

## Analysis Notes

- Hidden-gem rate is zero for this sample; inspect whether the metric is too strict or the sampled requests are biased toward mainstream categories.
- Category diversity is moderate to low in this sample, suggesting room to tune exploration or diversity-aware sampling.

## Sample Requests

- `Siem Reap` | 2 days | mode=`balanced` | activities=['Waterfall', 'Art Gallery']
- `Siem Reap` | 2 days | mode=`balanced` | activities=['Historical Site', 'Wildlife / Zoo']
- `Siem Reap` | 2 days | mode=`balanced` | activities=['Waterfall', 'Park / Nature']
