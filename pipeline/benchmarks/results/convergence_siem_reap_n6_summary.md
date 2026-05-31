# Benchmark Summary: Siem Reap n=6

- Generated: 2026-05-31T19:37:18
- Trials: 30

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 25.88 | 2.04 | 0.05 |
| Greedy NN | 20.18 | 2.84 | 0.08 |
| 2-opt | 19.23 | 2.43 | 0.26 |
| GA (basic) | 16.60 | 0.00 | 55.99 |
| GA (memetic) | 16.60 | 0.00 | 134.49 |

## Improvements

- GA (basic) vs Random: 35.85%
- GA (memetic) vs Random: 35.85%
- GA (memetic) vs 2-opt: 13.68%
- GA (memetic) vs GA (basic): 0.00%

## Statistical Tests

- `memetic_vs_basic`: p=1.000000, winner=GA (basic)
- `memetic_vs_2opt`: p=0.000283, winner=GA (memetic)
- `basic_vs_2opt`: p=0.000283, winner=GA (basic)

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.

## Report-Ready Claims

- For Siem Reap benchmark cases with n=6 places over 30 trials, the memetic GA achieved 13.68% shorter routes than deterministic 2-opt (Wilcoxon p=0.000283).
