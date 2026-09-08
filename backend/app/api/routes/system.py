"""System status — component health + pipeline vitals."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import DBSession, RedisClient
from app.core.config import settings
from app.services.simulator_control import get_status as simulator_status

router = APIRouter()

_STARTED_AT = time.time()


@router.get("/status")
async def system_status(session: DBSession, redis: RedisClient) -> dict:
    components: dict[str, dict] = {}

    t0 = time.perf_counter()
    try:
        await session.execute(text("SELECT 1"))
        components["postgres"] = {
            "status": "up",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as exc:  # noqa: BLE001
        components["postgres"] = {"status": "down", "error": type(exc).__name__}

    t0 = time.perf_counter()
    try:
        await redis.ping()
        components["redis"] = {
            "status": "up",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as exc:  # noqa: BLE001
        components["redis"] = {"status": "down", "error": type(exc).__name__}

    # Worker liveness — the pipeline stamps this hash roughly every 5s.
    rolling = await redis.hgetall("siem:metrics:rolling")
    worker_seen = await redis.get("siem:worker:heartbeat")
    worker_up = bool(worker_seen) and (time.time() - float(worker_seen) < 20)
    components["stream_processor"] = {
        "status": "up" if worker_up else "unknown",
        "events_per_second": float(rolling.get("events_per_second", 0) or 0),
    }

    sim = await simulator_status(redis)
    components["simulator"] = {
        "status": "up" if sim["simulator_connected"] else "idle",
        "scenario": sim["desired"].get("scenario"),
        "rate": sim["desired"].get("rate"),
        "running": sim["desired"].get("running"),
    }

    overall = (
        "healthy"
        if components["postgres"]["status"] == "up" and components["redis"]["status"] == "up"
        else "degraded"
    )
    return {
        "status": overall,
        "version": __version__,
        "env": settings.env,
        "uptime_seconds": round(time.time() - _STARTED_AT, 1),
        "generated_at": datetime.now(UTC).isoformat(),
        "broker": {
            "type": "redpanda (kafka-compatible)",
            "bootstrap_servers": settings.kafka_bootstrap_servers,
            "topic": settings.kafka_topic_events,
            "consumer_group": settings.kafka_consumer_group,
        },
        "feature_flags": {
            "ml": settings.enable_ml,
            "llm_assist": settings.enable_llm_assist,
            "auth": settings.auth_enabled,
            "enrichment_provider": settings.enrichment_provider,
        },
        "components": components,
    }
