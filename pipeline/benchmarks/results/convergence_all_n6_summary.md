# Benchmark Summary: Siem Reap n=6

- Generated: 2026-05-10T01:55:49
- Trials: 30

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 1133.56 | 231.81 | 0.02 |
| Greedy NN | 699.16 | 45.52 | 0.03 |
| 2-opt | 699.51 | 46.24 | 0.10 |
| GA (basic) | 665.22 | 23.92 | 17.70 |
| GA (memetic) | 655.83 | 0.00 | 42.61 |

## Improvements

- GA (basic) vs Random: 41.32%
- GA (memetic) vs Random: 42.14%
- GA (memetic) vs 2-opt: 6.24%
- GA (memetic) vs GA (basic): 1.41%

## Statistical Tests

- `memetic_vs_basic`: p=0.045500, winner=GA (memetic)
- `memetic_vs_2opt`: p=0.000062, winner=GA (memetic)
- `basic_vs_2opt`: p=0.000718, winner=GA (basic)

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.
- Mean memetic GA runtime stayed below 50 ms for this problem size, which is suitable for interactive trip generation.

## Report-Ready Claims

- For Siem Reap benchmark cases with n=6 places over 30 trials, the memetic GA achieved 6.24% shorter routes than deterministic 2-opt (Wilcoxon p=0.000062).
- Against the Week 1 baseline GA, the Week 2 memetic GA improved mean route length by 1.41% for Siem Reap n=6 cases.
