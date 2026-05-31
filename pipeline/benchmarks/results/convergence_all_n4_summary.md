# Benchmark Summary: Siem Reap n=4

- Generated: 2026-05-10T01:55:50
- Trials: 30

## Algorithm Metrics

| Algorithm | Mean km | Std km | Mean time (ms) |
|---|---:|---:|---:|
| Random | 751.56 | 110.12 | 0.02 |
| Greedy NN | 621.85 | 42.56 | 0.02 |
| 2-opt | 621.85 | 42.56 | 0.03 |
| GA (basic) | 575.41 | 0.00 | 9.39 |
| GA (memetic) | 575.41 | 0.00 | 17.40 |

## Improvements

- GA (basic) vs Random: 23.44%
- GA (memetic) vs Random: 23.44%
- GA (memetic) vs 2-opt: 7.47%
- GA (memetic) vs GA (basic): 0.00%

## Statistical Tests

- `memetic_vs_basic`: p=1.000000, winner=GA (basic)
- `memetic_vs_2opt`: p=0.000152, winner=GA (memetic)
- `basic_vs_2opt`: p=0.000152, winner=GA (basic)

## Analysis Notes

- GA (memetic) showed near-zero variance across seeds; verify whether deterministic seeding or problem simplicity is dominating.
- Memetic GA beat deterministic 2-opt on mean route length, suggesting the hybrid search adds value beyond local optimization alone.
- Mean memetic GA runtime stayed below 50 ms for this problem size, which is suitable for interactive trip generation.

## Report-Ready Claims

- For Siem Reap benchmark cases with n=4 places over 30 trials, the memetic GA achieved 7.47% shorter routes than deterministic 2-opt (Wilcoxon p=0.000152).
