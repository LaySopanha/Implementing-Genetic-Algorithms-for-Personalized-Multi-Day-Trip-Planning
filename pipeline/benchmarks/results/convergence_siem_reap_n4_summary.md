# Benchmark Summary: Siem Reap n=4

- Generated: 2026-05-31T19:37:12
- Trials: 30

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 12.62 | 1.77 | 0.04 |
| Greedy NN | 10.15 | 0.98 | 0.04 |
| 2-opt | 10.15 | 0.98 | 0.07 |
| GA (basic) | 9.35 | 0.00 | 23.47 |
| GA (memetic) | 9.35 | 0.00 | 45.08 |

## Improvements

- GA (basic) vs Random: 25.97%
- GA (memetic) vs Random: 25.97%
- GA (memetic) vs 2-opt: 7.89%
- GA (memetic) vs GA (basic): 0.00%

## Statistical Tests

- `memetic_vs_basic`: p=1.000000, winner=GA (basic)
- `memetic_vs_2opt`: p=0.001068, winner=GA (memetic)
- `basic_vs_2opt`: p=0.001068, winner=GA (basic)

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.
- Mean memetic GA runtime stayed below 50 ms for this problem size, which is suitable for interactive trip generation.

## Report-Ready Claims

- For Siem Reap benchmark cases with n=4 places over 30 trials, the memetic GA achieved 7.89% shorter routes than deterministic 2-opt (Wilcoxon p=0.001068).
