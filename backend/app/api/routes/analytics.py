"""Aggregated analytics for the Threat Activity, Analytics and Performance pages.

Each response bundles several durable aggregates so a page renders in one round
trip. Every value is a stored count or a measured metric.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import orjson
from fastapi import APIRouter, Query

from app.api.deps import DBSession, RedisClient
from app.detection.enrichment import get_enrichment_provider
from app.storage.repositories import AlertRepository, EventRepository

router = APIRouter()


@router.get("/threat-activity")
async def threat_activity(
    session: DBSession,
    minutes: int = Query(180, ge=15, le=1440),
    bucket_seconds: int = Query(300, ge=60, le=3600),
) -> dict:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    events_repo = EventRepository(session)
    alerts_repo = AlertRepository(session)
    provider = get_enrichment_provider()

    top_ip_rows = await events_repo.top_source_ips(since, 10)
    top_ips = []
    for row in top_ip_rows:
        enr = await provider.enrich(row["source_ip"])
        top_ips.append({**row, "enrichment": enr.as_dict()})

    return {
        "window_minutes": minutes,
        "events_timeseries": await events_repo.timeseries(since, bucket_seconds),
        "alerts_timeseries": await alerts_repo.timeseries(since, max(bucket_seconds, 300)),
        "event_severity": await events_repo.severity_breakdown(since),
        "event_types": await events_repo.event_type_breakdown(since),
        "rule_frequency": [
            {
                "rule_id": rid,
                "trigger_count": v["trigger_count"],
                "last_triggered": v["last_triggered"],
            }
            for rid, v in sorted(
                (await alerts_repo.rule_activity()).items(),
                key=lambda kv: -kv[1]["trigger_count"],
            )
        ],
        "top_source_ips": top_ips,
        "top_attacked_hosts": await alerts_repo.affected_hosts(since, 10),
        "top_event_sources": await events_repo.top_hosts(since, 10),
    }


@router.get("/heatmap")
async def heatmap(
    session: DBSession,
    hours: int = Query(24, ge=2, le=168),
) -> dict:
    since = datetime.now(UTC) - timedelta(hours=hours)
    cells = await AlertRepository(session).severity_heatmap(since, 3600)
    total = sum(c["count"] for c in cells)
    return {
        "available": total >= 12,  # not enough signal to be meaningful below this
        "hours": hours,
        "bucket_seconds": 3600,
        "severities": ["critical", "high", "medium", "low", "info"],
        "cells": cells,
        "total": total,
    }


@router.get("/performance")
async def performance(redis: RedisClient) -> dict:
    rolling = await redis.hgetall("siem:metrics:rolling")
    raw_history = await redis.lrange("siem:metrics:history", 0, 240)
    history = []
    for row in reversed(raw_history):
        try:
            history.append(orjson.loads(row))
        except orjson.JSONDecodeError:
            continue
    lag = await redis.hgetall("siem:metrics:consumer_lag")

    def num(v):
        try:
            f = float(v)
            return int(f) if f.is_integer() else f
        except (TypeError, ValueError):
            return None

    return {
        "current": {k: num(v) for k, v in rolling.items()},
        "consumer_lag": num(lag.get("lag")),
        "history": history,
        "samples": len(history),
    }
