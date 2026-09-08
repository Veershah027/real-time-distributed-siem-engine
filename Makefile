# Real-Time Distributed Enterprise SIEM Engine
.DEFAULT_GOAL := help
COMPOSE := docker compose
DC_DEV  := docker compose -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## ---- stack ----
.PHONY: up down reset logs ps restart
up: ## Build + start the whole stack (detached)
	cp -n .env.example .env || true
	$(COMPOSE) up -d --build

dev: ## Start with the dev override (backend code mounted)
	cp -n .env.example .env || true
	$(DC_DEV) up --build

down: ## Stop the stack
	$(COMPOSE) down

reset: ## Stop the stack and wipe all volumes
	$(COMPOSE) down -v

logs: ## Follow all logs
	$(COMPOSE) logs -f

ps: ## Service status
	$(COMPOSE) ps

restart: ## Restart backend + worker
	$(COMPOSE) restart backend worker

## ---- quality ----
.PHONY: lint test test-int fmt
lint: ## ruff + mypy (backend) + eslint (frontend)
	cd backend && ruff check . && ruff format --check . && mypy app
	cd simulator && ruff check .
	cd frontend && npm run lint && npm run typecheck

fmt: ## Auto-format backend + simulator
	cd backend && ruff check . --fix && ruff format .
	cd simulator && ruff check . --fix && ruff format .

test: ## Backend + simulator unit tests (no infra)
	cd backend && pytest -m "not integration"
	cd simulator && pytest

test-int: ## Full backend suite incl. integration (boots postgres+redis)
	$(COMPOSE) up -d postgres redis
	cd backend && SIEM_RUN_INTEGRATION=1 pytest

## ---- demo ----
.PHONY: sim-brute sim-scan sim-mixed bench
sim-brute: ## Fire one SSH brute-force scenario at the running stack
	$(COMPOSE) run --rm simulator --once ssh_brute_force

sim-scan: ## Fire one port-scan scenario
	$(COMPOSE) run --rm simulator --once port_scan

sim-mixed: ## Switch the live simulator to mixed attack traffic
	curl -fsS -XPOST localhost:8000/api/simulator/start \
	  -H 'content-type: application/json' -d '{"scenario":"mixed","rate":120}'

bench: ## Run the throughput benchmark against the running stack
	python benchmarks/throughput.py --duration 30 --rate 1000
