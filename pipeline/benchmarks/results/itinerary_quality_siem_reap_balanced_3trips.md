# Itinerary Quality Evaluation

- Generated: 2026-05-08T16:12:36
- Trips evaluated: 3
- Coverage: 44.00%

## Aggregate Metrics

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| diversity_entropy | 0.8563 | 0.0637 | 0.8113 | 0.9464 |
| spatial_efficiency_km_per_activity | 2.7917 | 2.3067 | 0.8000 | 6.0250 |
| score_density | 3.0421 | 0.1071 | 2.9021 | 3.1622 |
| hidden_gem_rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| total_distance_km | 11.1667 | 9.2269 | 3.2000 | 24.1000 |

## Analysis Notes

- Hidden-gem rate is zero for this sample; inspect whether the metric is too strict or the sampled requests are biased toward mainstream categories.

## Sample Requests

- `Siem Reap` | 2 days | mode=`balanced` | activities=['Local Markets', 'Aquarium']
- `Siem Reap` | 2 days | mode=`balanced` | activities=['Park / Nature', 'Local Markets']
- `Siem Reap` | 2 days | mode=`balanced` | activities=['Local Markets', 'Nightlife / Bars']
