"""Aggregates dashboard metrics from Redis (real-time) + Postgres (durable)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.enums import AlertStatus
from app.storage.repositories import AlertRepository, EventRepository


async def _redis_float(client: redis.Redis, key: str, field: str, default: float = 0.0) -> float:
    val = await client.hget(key, field)
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


async def dashboard_metrics(session: AsyncSession, client: redis.Redis) -> dict[str, Any]:
    now = datetime.now(UTC)
    events_repo = EventRepository(session)
    alerts_repo = AlertRepository(session)

    eps = await _redis_float(client, "siem:metrics:rolling", "events_per_second")
    last_minute = await client.hgetall("siem:metrics:last_minute")

    events_1h = await events_repo.count_since(now - timedelta(hours=1))
    events_24h = await events_repo.count_since(now - timedelta(hours=24))

    counts = await alerts_repo.counts_by_status_severity()
    active = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    total_active = 0
    resolved = 0
    false_positive = 0
    for key, n in counts.items():
        status, sev = key.split(":")
        if status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED):
            active[sev] = active.get(sev, 0) + n
            total_active += n
        elif status == AlertStatus.RESOLVED:
            resolved += n
        elif status == AlertStatus.FALSE_POSITIVE:
            false_positive += n

    total_alerts = sum(counts.values())
    detection_rate = round(total_alerts / events_24h, 5) if events_24h else 0.0
    fp_rate = round(false_positive / total_alerts, 3) if total_alerts else 0.0

    return {
        "generated_at": now.isoformat(),
        "events_per_second": round(eps, 2),
        "events_last_hour": events_1h,
        "events_last_24h": events_24h,
        "last_minute": {k: _num(v) for k, v in last_minute.items() if k != "minute"},
        "active_alerts_total": total_active,
        "active_alerts_by_severity": active,
        "critical_alerts": active.get("critical", 0),
        "high_alerts": active.get("high", 0),
        "resolved_alerts": resolved,
        "false_positive_alerts": false_positive,
        "total_alerts": total_alerts,
        "detection_rate": detection_rate,
        "false_positive_rate": fp_rate,
    }


def _num(v: str) -> float | int:
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return 0
