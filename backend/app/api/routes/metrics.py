"""Dashboard metrics + Prometheus exposition."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.deps import DBSession, RedisClient
from app.core.metrics import REGISTRY
from app.services.metrics_service import dashboard_metrics
from app.storage.repositories import AlertRepository, EventRepository

router = APIRouter()


@router.get("/metrics")
async def metrics(session: DBSession, redis: RedisClient) -> dict:
    """Aggregated dashboard metrics (JSON)."""
    return await dashboard_metrics(session, redis)


@router.get("/metrics/timeseries")
async def timeseries(
    session: DBSession,
    minutes: int = Query(60, ge=5, le=1440),
    bucket_seconds: int = Query(60, ge=30, le=3600),
) -> dict:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    events = await EventRepository(session).timeseries(since, bucket_seconds)
    alerts = await AlertRepository(session).timeseries(since, max(bucket_seconds, 300))
    return {"window_minutes": minutes, "events": events, "alerts": alerts}


@router.get("/prometheus", include_in_schema=False)
async def prometheus() -> Response:
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
