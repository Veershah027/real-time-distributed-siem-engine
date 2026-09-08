# Infrastructure

Local orchestration is entirely in the root `docker-compose.yml` (+
`docker-compose.dev.yml`). This directory holds supporting assets and notes.

## `configs/`

- `redpanda-bootstrap.md` — how the topic is created and how to inspect the
  broker with `rpk`.
- `prometheus.example.yml` — a scrape config you can point a local Prometheus at
  (`http://localhost:8000/metrics`). Not wired into compose by default to keep
  the stack lean.

## `docker/`

Reserved for alternate Dockerfiles / target-specific overrides. The primary
images are `backend/Dockerfile`, `simulator/Dockerfile`, and
`frontend/Dockerfile`.

## Service topology (compose)

| Service | Image | Role | Host port (127.0.0.1) |
|---|---|---|---|
| `redpanda` | redpandadata/redpanda | Kafka-compatible broker | 19092, 9644 |
| `redpanda-init` | redpandadata/redpanda | one-shot: create the topic | — |
| `postgres` | postgres:16-alpine | durable store | 5432 |
| `redis` | redis:7-alpine | ephemeral state + pub/sub | 6379 |
| `backend` | siem-engine/backend | FastAPI (migrations + API) | 8000 |
| `worker` | siem-engine/backend | stream processor | — |
| `simulator` | siem-engine/simulator | synthetic log producer | — |
| `frontend` | siem-engine/frontend | nginx + SPA + API/WS proxy | 8080 |
