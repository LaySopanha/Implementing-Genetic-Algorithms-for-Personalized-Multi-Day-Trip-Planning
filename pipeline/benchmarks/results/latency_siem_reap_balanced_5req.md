# Latency Benchmark

- Generated: 2026-05-08T16:12:37
- Requests benchmarked: 5

## Latency Metrics

| Metric | ms |
|---|---:|
| mean | 1988.0489 |
| std | 1983.8438 |
| min | 616.0759 |
| max | 5902.1049 |
| p50 | 913.3297 |
| p95 | 5042.4770 |
| p99 | 5730.1793 |

## Analysis Notes

- p95 latency exceeds the 2-second UX target and should be profiled before production use.
- High tail latency relative to p50 suggests request-level variance worth profiling.

## Sample Requests

- `Siem Reap` | 2 days | mode=`balanced` | latency=1603.97 ms
- `Siem Reap` | 2 days | mode=`balanced` | latency=904.77 ms
- `Siem Reap` | 2 days | mode=`balanced` | latency=5902.10 ms
- `Siem Reap` | 2 days | mode=`balanced` | latency=913.33 ms
- `Siem Reap` | 2 days | mode=`balanced` | latency=616.08 ms
