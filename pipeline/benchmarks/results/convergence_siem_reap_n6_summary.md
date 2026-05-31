# Benchmark Summary: Siem Reap n=6

- Generated: 2026-05-08T16:07:54
- Trials: 5

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 24.98 | 0.76 | 0.16 |
| Greedy NN | 18.72 | 2.61 | 0.22 |
| 2-opt | 18.54 | 2.38 | 0.85 |
| GA (basic) | 16.60 | 0.00 | 137.57 |
| GA (memetic) | 16.60 | 0.00 | 375.54 |

## Improvements

- GA (basic) vs Random: 33.54%
- GA (memetic) vs Random: 33.54%
- GA (memetic) vs 2-opt: 10.48%
- GA (memetic) vs GA (basic): 0.00%

## Statistical Tests

- Wilcoxon tests not available in this environment.

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.

## Report-Ready Claims

- No statistically backed claim generated automatically.
