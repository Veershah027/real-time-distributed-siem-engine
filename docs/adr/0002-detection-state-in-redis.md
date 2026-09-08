# ADR 0002 — Detector state lives in Redis, not process memory

- **Status:** Accepted
- **Date:** 2026-09-07
- **Context:** rule detectors are inherently stateful — "> 10 failures from one
  IP in 60s" needs a sliding window of recent events per source IP. Where should
  that state live?

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **In-process dicts / `collections.deque`** | Zero infra; fastest. | State is lost on restart; a second worker double-counts or misses; no horizontal scaling; memory grows with cardinality. |
| **Postgres** | Durable; already present. | A write + range-scan per event is far too heavy at target rates; churns the WAL. |
| **Redis sorted sets (ZSET) per window** | O(log n) add/trim; TTL auto-expiry; shared across workers; already present for pub/sub and metrics. | One extra round trip per detector (mitigated with pipelines). |

## Decision

Keep **all** cross-event detector state in Redis via
`app.detection.windows.WindowStore`. Each window is a ZSET keyed
`siem:win:<name>:<entity>`; score = event epoch seconds; member =
`"<value>\x1f<random token>"` (the token guarantees uniqueness when two events
share a timestamp and value). `add_and_measure` does trim + add + expire + range
in **one pipelined round trip** and returns count, unique-value set, and span.

Detectors themselves are stateless objects. The `DetectionEngine` holds no
per-event state.

## Consequences

- **Positive:** workers are stateless and horizontally scalable — run N
  replicas in the same consumer group and windows stay correct.
- **Positive:** a worker restart loses nothing; windows self-heal within one
  window duration.
- **Positive:** memory is bounded by Redis `maxmemory` + `allkeys-lru`, not by
  unique-IP cardinality in a Python process.
- **Negative:** detection correctness now depends on Redis availability. If Redis
  is down, detectors degrade (the engine logs and continues); rule-based alerts
  pause rather than produce wrong results.
- **Negative:** one Redis round trip per applicable detector per event. At the
  demo's target rates this is comfortably within budget; `siem_detection_latency_seconds`
  makes it observable.
