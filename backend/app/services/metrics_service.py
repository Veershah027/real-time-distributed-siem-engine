"""Aggregates dashboard metrics from Redis (real-time) + Postgres (durable).

Every field is either a stored count, a measured rate/latency written by the
stream processor, or `null` when the source is unavailable. Nothing is
synthesised.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.enums import AlertStatus
from app.storage.repositories import AlertRepository, EventRepository

_ROLLING = "siem:metrics:rolling"


def _num(v: Any) -> float | int:
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return 0


async def dashboard_metrics(session: AsyncSession, client: redis.Redis) -> dict[str, Any]:
    now = datetime.now(UTC)
    events_repo = EventRepository(session)
    alerts_repo = AlertRepository(session)

    rolling = await client.hgetall(_ROLLING)
    last_minute = await client.hgetall("siem:metrics:last_minute")
    worker_seen = await client.get("siem:worker:heartbeat")
    lag_raw = await client.hgetall("siem:metrics:consumer_lag")

    worker_fresh = bool(worker_seen) and (time.time() - float(worker_seen) < 20)
    rolling_fresh = (
        worker_fresh
        and "updated_at" in rolling
        and (time.time() - float(rolling.get("updated_at", 0)) < 30)
    )

    def rv(key: str) -> float | int | None:
        return _num(rolling[key]) if rolling_fresh and key in rolling else None

    events_1h = await events_repo.count_since(now - timedelta(hours=1))
    events_24h = await events_repo.count_since(now - timedelta(hours=24))

    counts = await alerts_repo.counts_by_status_severity()
    active = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    total_active = resolved = false_positive = investigating = acknowledged = 0
    for key, n in counts.items():
        status, sev = key.split(":")
        if AlertStatus(status).is_active:
            active[sev] = active.get(sev, 0) + n
            total_active += n
            if status == AlertStatus.INVESTIGATING:
                investigating += n
            elif status == AlertStatus.ACKNOWLEDGED:
                acknowledged += n
        elif status == AlertStatus.RESOLVED:
            resolved += n
        elif status == AlertStatus.FALSE_POSITIVE:
            false_positive += n

    total_alerts = sum(counts.values())
    detection_rate = round(total_alerts / events_24h, 5) if events_24h else 0.0
    fp_rate = round(false_positive / total_alerts, 3) if total_alerts else 0.0

    consumer_lag = _num(lag_raw["lag"]) if lag_raw.get("lag") is not None else None

    return {
        "generated_at": now.isoformat(),
        "worker_online": worker_fresh,
        # --- throughput / latency (measured by the stream processor; null if stale) ---
        "events_per_second": rv("events_per_second"),
        "events_processed_per_second": rv("events_processed_per_second"),
        "pipeline_latency_ms": rv("pipeline_latency_ms"),
        "detection_latency_ms": rv("detection_latency_ms"),
        "alerts_per_minute": rv("alerts_per_minute"),
        "pipeline_health_pct": rv("pipeline_health_pct"),
        "invalid_events_window": rv("invalid_events_window"),
        "duplicate_events_window": rv("duplicate_events_window"),
        "consumer_lag": consumer_lag,
        # --- durable counts ---
        "events_last_hour": events_1h,
        "events_last_24h": events_24h,
        "last_minute": {k: _num(v) for k, v in last_minute.items() if k != "minute"},
        # --- alerts ---
        "active_alerts_total": total_active,
        "active_alerts_by_severity": active,
        "critical_alerts": active.get("critical", 0),
        "high_alerts": active.get("high", 0),
        "acknowledged_alerts": acknowledged,
        "investigating_alerts": investigating,
        "resolved_alerts": resolved,
        "false_positive_alerts": false_positive,
        "total_alerts": total_alerts,
        "detection_rate": detection_rate,
        "false_positive_rate": fp_rate,
    }
