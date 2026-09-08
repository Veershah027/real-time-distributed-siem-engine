# Development Guide

## Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| Docker Desktop / Engine + Compose v2 | recent | the full stack |
| Python | 3.11+ (3.12 in CI/images) | backend & simulator dev |
| Node.js | 22+ | frontend dev |
| Git | any | version control |

## Repository layout

```
real-time-distributed-siem-engine/
├── backend/            FastAPI API + stream processor + detection engine
│   ├── app/
│   │   ├── api/         routes + deps
│   │   ├── core/        config, logging, security, metrics
│   │   ├── detection/   engine, rules/, anomaly, ml, correlation, enrichment, windows
│   │   ├── models/      SQLAlchemy ORM
│   │   ├── schemas/     Pydantic models + enums
│   │   ├── services/    alert triage, metrics aggregation, simulator control
│   │   ├── storage/     async engine, redis client, repositories
│   │   ├── streaming/   kafka wrappers, pipeline
│   │   ├── main.py      API app factory
│   │   ├── worker.py    stream-processor entrypoint
│   │   └── seed.py      detection-rule catalogue seeding
│   ├── alembic/         migrations
│   └── tests/
├── simulator/          synthetic enterprise log generator + attack scenarios
│   └── simulator/{generators,scenarios,producers}/
├── frontend/           React + TS SOC dashboard
│   └── src/{components,pages,hooks,services,lib,types}/
├── detection-rules/    YAML rule reference (mirrors code defaults)
├── infrastructure/     redpanda / config assets
├── docs/               architecture, detection-rules, threat-model, adr/
├── benchmarks/         throughput.py
├── .github/workflows/  ci.yml
├── docker-compose.yml  + docker-compose.dev.yml
└── Makefile
```

## Running the stack

```bash
cp .env.example .env
docker compose up --build          # first run
docker compose up -d               # detached
docker compose logs -f worker      # follow the stream processor
docker compose ps                  # health of every service
docker compose down                # stop
docker compose down -v             # stop + wipe volumes (full reset)
```

Ports (all bound to `127.0.0.1`): dashboard `8080`, API `8000`, Postgres `5432`,
Redis `6379`, Redpanda `19092` (Kafka) / `9644` (admin).

### Makefile shortcuts

```bash
make up            # docker compose up -d --build
make down          # docker compose down
make reset         # docker compose down -v
make logs          # follow all logs
make ps            # service status
make test          # backend unit tests (no infra)
make test-int      # backend integration tests (boots postgres+redis)
make lint          # ruff + mypy + eslint
make sim-brute     # one-shot SSH brute-force scenario
make sim-scan      # one-shot port-scan scenario
make bench         # run benchmarks/throughput.py
```

## Backend development

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate     # or bin/activate on *nix
pip install -e ".[dev]"          # add ",ml" for the Isolation Forest extra

ruff check . && ruff format --check .
mypy app
bandit -c pyproject.toml -r app
pytest -m "not integration"      # fast, uses fakeredis

# integration + API tests
docker compose up -d postgres redis
SIEM_RUN_INTEGRATION=1 pytest
```

### Hot-reload against the containerised infra

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

The backend `app/` directory is mounted read-only; Uvicorn is **not** in reload
mode by default (the entrypoint runs migrations then `uvicorn`). For an
auto-reloading loop, run the API on the host instead:

```bash
cd backend
POSTGRES_HOST=localhost REDIS_HOST=localhost \
SIEM_KAFKA_BOOTSTRAP_SERVERS=localhost:19092 \
uvicorn app.main:app --reload
# and the worker:
POSTGRES_HOST=localhost REDIS_HOST=localhost \
SIEM_KAFKA_BOOTSTRAP_SERVERS=localhost:19092 python -m app.worker
```

### Migrations

```bash
cd backend
alembic revision --autogenerate -m "add X"
alembic upgrade head
alembic downgrade -1
```

`alembic/env.py` reads the DB URL from `app.core.config`, so set
`POSTGRES_HOST=localhost` (etc.) when running against the compose Postgres.

## Frontend development

```bash
cd frontend
npm install
npm run dev            # Vite dev server on :5173, proxies /api and /ws to :8000
npm run lint
npm run typecheck
npm test               # Vitest
npm run build          # tsc --noEmit && vite build
```

`VITE_API_BASE_URL` empty ⇒ same-origin (works behind the nginx proxy in the
image). For `npm run dev`, the Vite proxy handles it.

## Simulator

```bash
cd simulator
pip install -e ".[dev]"
python -m simulator --help
python -m simulator --rate 200 --sink console    # no broker needed
python -m simulator --once ssh_brute_force        # against the running stack
pytest
```

## Environment variables

Every setting is documented in [`.env.example`](../.env.example). The important
knobs: `SIEM_EVENTS_PER_SECOND`, `SIEM_SIMULATOR_SCENARIO`, the
`SIEM_RULE_*` thresholds, `SIEM_ANOMALY_*`, `SIEM_ENABLE_ML`,
`SIEM_AUTH_ENABLED`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `worker` restarts / "could not connect to Kafka" | Redpanda not healthy yet — `docker compose logs redpanda`; the worker retries for ~2 min. |
| No events on the dashboard | check `docker compose logs simulator`; ensure `redpanda-init` created the topic (`docker compose logs redpanda-init`). |
| Dashboard "Reconnecting…" | backend not up or `/ws` blocked; `curl localhost:8000/health`. |
| `alembic upgrade` fails locally | you didn't set `POSTGRES_HOST=localhost`. |
| Port already in use | something else owns 8000/8080/5432/6379/19092 — stop it or edit compose port maps. |
| Integration tests all skipped | set `SIEM_RUN_INTEGRATION=1` and have Postgres+Redis reachable. |
