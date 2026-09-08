"""Threat analytics + enrichment."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DBSession
from app.detection.enrichment import get_enrichment_provider
from app.storage.repositories import EventRepository

router = APIRouter()


@router.get("/top-ips")
async def top_ips(
    session: DBSession,
    minutes: int = Query(60, ge=5, le=1440),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    repo = EventRepository(session)
    rows = await repo.top_source_ips(since, limit)
    provider = get_enrichment_provider()
    enriched = []
    for row in rows:
        e = await provider.enrich(row["source_ip"])
        enriched.append({**row, "enrichment": e.as_dict()})
    return {"window_minutes": minutes, "items": enriched}


@router.get("/event-types")
async def event_types(session: DBSession, minutes: int = Query(60, ge=5, le=1440)) -> dict:
    since = datetime.now(UTC) - timedelta(minutes=minutes)
    breakdown = await EventRepository(session).event_type_breakdown(since)
    return {"window_minutes": minutes, "items": breakdown}


@router.get("/enrich/{ip}")
async def enrich_ip(ip: str) -> dict:
    try:
        ipaddress.ip_address(ip)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid IP address") from exc
    provider = get_enrichment_provider()
    return (await provider.enrich(ip)).as_dict()
