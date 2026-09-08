"""Event query API."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DBSession, PaginationDep
from app.schemas.common import Page
from app.schemas.event import EventRead
from app.storage.repositories import EventRepository

router = APIRouter()


@router.get("", response_model=Page[EventRead])
async def list_events(
    session: DBSession,
    page: PaginationDep,
    event_type: str | None = Query(None),
    source_ip: str | None = Query(None),
    severity: str | None = Query(None),
    source: str | None = Query(None),
    username: str | None = Query(None),
    q: str | None = Query(None, max_length=200, description="substring match on message"),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
) -> Page[EventRead]:
    repo = EventRepository(session)
    rows, total = await repo.list(
        limit=page.limit,
        offset=page.offset,
        event_type=event_type,
        source_ip=source_ip,
        severity=severity,
        source=source,
        username=username,
        q=q,
        start=start,
        end=end,
    )
    items = [EventRead.model_validate(_row_to_dict(r)) for r in rows]
    return Page(items=items, total=total, limit=page.limit, offset=page.offset)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: uuid.UUID, session: DBSession) -> EventRead:
    repo = EventRepository(session)
    row = await repo.get(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    return EventRead.model_validate(_row_to_dict(row))


def _row_to_dict(row) -> dict:
    return {
        "event_id": row.event_id,
        "timestamp": row.timestamp,
        "ingested_at": row.ingested_at,
        "source": row.source,
        "source_type": row.source_type,
        "event_type": row.event_type,
        "source_ip": row.source_ip,
        "destination_ip": row.destination_ip,
        "destination_port": row.destination_port,
        "username": row.username,
        "service": row.service,
        "action": row.action,
        "status": row.status,
        "severity": row.severity,
        "message": row.message,
        "bytes_out": row.bytes_out,
        "bytes_in": row.bytes_in,
        "metadata": row.event_metadata,
    }
