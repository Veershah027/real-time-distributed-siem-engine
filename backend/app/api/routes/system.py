"""System status — component health + pipeline vitals."""

from __future__ import annotations

import asyncio
import socket
import time
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import DBSession, RedisClient
from app.core.config import settings
from app.services.simulator_control import get_status as simulator_status

router = APIRouter()

_STARTED_AT = time.time()


async def _tcp_ok(host: str, port: int, deadline: float = 2.0) -> bool:
    try:
        async with asyncio.timeout(deadline):
            _, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, TimeoutError, socket.gaierror):
        return False


async def _http_ok(url: str, deadline: float = 2.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=deadline) as c:
            return (await c.get(url)).status_code < 500
    except Exception:
        return False


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
    except Exception as exc:
        components["postgres"] = {"status": "down", "error": type(exc).__name__}

    t0 = time.perf_counter()
    try:
        await redis.ping()
        components["redis"] = {
            "status": "up",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as exc:
        components["redis"] = {"status": "down", "error": type(exc).__name__}

    # Worker liveness — the pipeline stamps this hash roughly every 5s.
    rolling = await redis.hgetall("siem:metrics:rolling")
    lag_raw = await redis.hgetall("siem:metrics:consumer_lag")
    worker_seen = await redis.get("siem:worker:heartbeat")
    worker_up = bool(worker_seen) and (time.time() - float(worker_seen) < 20)

    def _f(key: str) -> float | None:
        try:
            return round(float(rolling[key]), 3) if key in rolling else None
        except (TypeError, ValueError):
            return None

    components["stream_processor"] = {
        "status": "up" if worker_up else "unknown",
        "events_per_second": _f("events_per_second"),
        "events_processed_per_second": _f("events_processed_per_second"),
        "pipeline_latency_ms": _f("pipeline_latency_ms"),
        "detection_latency_ms": _f("detection_latency_ms"),
        "pipeline_health_pct": _f("pipeline_health_pct"),
        "consumer_lag": int(float(lag_raw["lag"])) if lag_raw.get("lag") is not None else None,
        "metrics_port": settings.worker_metrics_port,
    }

    # broker + frontend reachability (best-effort, short timeout)
    bootstrap = settings.kafka_bootstrap_servers.split(",")[0]
    b_host, _, b_port = bootstrap.partition(":")
    redpanda_up = await _tcp_ok(b_host, int(b_port or 9092))
    components["redpanda"] = {"status": "up" if redpanda_up else "down", "endpoint": bootstrap}
    frontend_up = await _http_ok("http://frontend:8080/nginx-health")
    components["frontend"] = {"status": "up" if frontend_up else "unknown"}
    components["api"] = {"status": "up", "uptime_seconds": round(time.time() - _STARTED_AT, 1)}

    sim = await simulator_status(redis)
    components["simulator"] = {
        "status": "up" if sim["simulator_connected"] else "idle",
        "scenario": sim["desired"].get("scenario"),
        "rate": sim["desired"].get("rate"),
        "running": sim["desired"].get("running"),
    }

    core_up = (
        components["postgres"]["status"] == "up"
        and components["redis"]["status"] == "up"
        and redpanda_up
    )
    overall = "healthy" if core_up and worker_up else "degraded" if core_up else "down"
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
