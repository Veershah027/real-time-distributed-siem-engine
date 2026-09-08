# Implementation Plan — Real-Time Distributed Enterprise SIEM Engine

Internal working plan. Tracks architectural decisions and build phases.

## Architectural decisions (summary — see `docs/architecture.md` + ADRs)

| Decision | Choice | Rationale |
|---|---|---|
| Message broker | **Redpanda** (Kafka API compatible) | Single binary, no ZooKeeper/KRaft ceremony, ~1 GB lighter than Kafka for local dev. Same wire protocol, so `aiokafka` client and all code are Kafka-portable. |
| Kafka client | `aiokafka` | Mature async Kafka client, integrates with asyncio pipeline. |
| Web framework | FastAPI + Pydantic v2 | Async, typed, OpenAPI out of the box. |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic + asyncpg | Standard, typed, async driver. |
| Cache / RT state | Redis (`redis.asyncio`) | Sliding-window counters (sorted sets), detector state, pub/sub fan-out to WebSocket. |
| Real-time transport | WebSocket (`/ws`) fed by Redis pub/sub | Bi-directional not needed but WS is the SOC-dashboard standard; SSE fallback documented. |
| Anomaly detection | EWMA mean/variance + z-score (`detection/anomaly.py`) | Deterministic, explainable, no training. Optional IsolationForest behind `SIEM_ENABLE_ML`. |
| Frontend | React 18 + TS + Vite + Tailwind + Recharts + React Router | Fast dev loop, professional charts. |
| Stream processor | Separate process (`python -m app.worker`), same image as API | True producer→broker→consumer separation; scales independently in compose. |

## Event flow

```
simulator (producer) --JSON--> Redpanda topic `siem.events.raw`
    --> worker consumer --> validate (Pydantic) --> normalize
    --> DetectionEngine (rules + anomaly) --> AlertCorrelator
    --> PostgreSQL (events, alerts)  + Redis (windows, metrics, pub/sub)
    --> FastAPI REST + WebSocket --> React SOC dashboard
```

## Build phases

1. [x] Repo scaffold, git identity, .gitignore, LICENSE, .env.example
2. [x] Backend core: config, logging, security middleware, metrics
3. [x] Schemas (event, alert) + SQLAlchemy models + Alembic
4. [x] Storage: async DB session, Redis client, repositories (paginated)
5. [x] Streaming: Kafka producer/consumer wrappers, pipeline
6. [x] Detection engine: base interface, 7 rules, anomaly, correlation, enrichment
7. [x] API: health, events, alerts, metrics, threats, detections, system, simulator, websocket
8. [x] Simulator: models, generators, 7 attack scenarios, rate engine, CLI
9. [x] Frontend: layout, dashboard, events, alerts, rules, threat-intel, system, simulator pages
10. [x] Docker + docker-compose (+ dev override)
11. [x] Tests: unit (detectors, validation, correlation), API, integration
12. [x] CI: GitHub Actions (lint, type, test, coverage, bandit, pip-audit, frontend build, docker build)
13. [x] Docs: architecture, detection-rules, threat-model, development, ADRs
14. [x] End-to-end verification against running stack
15. [x] Push to GitHub, verify Actions

## Honesty ledger (things that are simulated / demo-grade)

- Enterprise logs are synthetic (the simulator is intentional project scope).
- No real endpoint agents, no real netflow.
- Threat-intel enrichment is a deterministic synthetic provider by default.
- Detection rules are demonstration rules with configurable thresholds, not a tuned production ruleset.
- Anomaly layer is a statistical baseline, not a production IDS/UEBA.
- Local Docker Compose is not a production deployment topology.
