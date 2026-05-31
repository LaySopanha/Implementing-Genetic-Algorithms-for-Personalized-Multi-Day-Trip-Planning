# Benchmark Summary: Siem Reap n=8

- Generated: 2026-05-31T19:37:10
- Trials: 30

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 30.04 | 3.07 | 0.07 |
| Greedy NN | 23.65 | 1.82 | 0.08 |
| 2-opt | 21.44 | 1.78 | 0.61 |
| GA (basic) | 18.50 | 0.63 | 61.75 |
| GA (memetic) | 18.23 | 0.00 | 180.72 |

## Improvements

- GA (basic) vs Random: 38.43%
- GA (memetic) vs Random: 39.33%
- GA (memetic) vs 2-opt: 14.97%
- GA (memetic) vs GA (basic): 1.46%

## Statistical Tests

- `memetic_vs_basic`: p=0.038434, winner=GA (memetic)
- `memetic_vs_2opt`: p=0.000018, winner=GA (memetic)
- `basic_vs_2opt`: p=0.000014, winner=GA (basic)

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.

## Report-Ready Claims

- For Siem Reap benchmark cases with n=8 places over 30 trials, the memetic GA achieved 14.97% shorter routes than deterministic 2-opt (Wilcoxon p=0.000018).
- Against the Week 1 baseline GA, the Week 2 memetic GA improved mean route length by 1.46% for Siem Reap n=8 cases.
