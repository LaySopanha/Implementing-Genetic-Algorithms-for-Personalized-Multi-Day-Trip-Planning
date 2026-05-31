# Benchmark Summary: Siem Reap n=8

- Generated: 2026-05-10T01:55:54
- Trials: 30

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 1515.85 | 221.26 | 0.02 |
| Greedy NN | 765.84 | 79.05 | 0.04 |
| 2-opt | 763.99 | 77.74 | 0.31 |
| GA (basic) | 722.68 | 76.23 | 32.89 |
| GA (memetic) | 669.33 | 0.00 | 86.74 |

## Improvements

- GA (basic) vs Random: 52.33%
- GA (memetic) vs Random: 55.84%
- GA (memetic) vs 2-opt: 12.39%
- GA (memetic) vs GA (basic): 7.38%

## Statistical Tests

- `memetic_vs_basic`: p=0.004809, winner=GA (memetic)
- `memetic_vs_2opt`: p=0.000036, winner=GA (memetic)
- `basic_vs_2opt`: p=0.013306, winner=GA (basic)

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.

## Report-Ready Claims

- For Siem Reap benchmark cases with n=8 places over 30 trials, the memetic GA achieved 12.39% shorter routes than deterministic 2-opt (Wilcoxon p=0.000036).
- Against the Week 1 baseline GA, the Week 2 memetic GA improved mean route length by 7.38% for Siem Reap n=8 cases.
