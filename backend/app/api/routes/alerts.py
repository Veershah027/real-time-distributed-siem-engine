"""Alert query + triage API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.deps import DBSession, PaginationDep, Principal, RedisClient
from app.schemas.alert import AlertRead, AlertUpdate
from app.schemas.common import Page
from app.schemas.enums import AlertStatus
from app.services.alerts import InvalidTransition, update_alert_status
from app.storage.redis_client import CHANNEL_ALERTS
from app.storage.repositories import AlertRepository, EventRepository

router = APIRouter()


@router.get("", response_model=Page[AlertRead])
async def list_alerts(
    session: DBSession,
    page: PaginationDep,
    status: AlertStatus | None = Query(None),
    severity: str | None = Query(None),
    rule_id: str | None = Query(None),
    source_ip: str | None = Query(None),
) -> Page[AlertRead]:
    repo = AlertRepository(session)
    rows, total = await repo.search(
        status=status.value if status else None,
        severity=severity,
        rule_id=rule_id,
        source_ip=source_ip,
        limit=page.limit,
        offset=page.offset,
    )
    return Page(
        items=[AlertRead.model_validate(r) for r in rows],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(alert_id: uuid.UUID, session: DBSession) -> AlertRead:
    alert = await AlertRepository(session).get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return AlertRead.model_validate(alert)


@router.get("/{alert_id}/events")
async def alert_related_events(alert_id: uuid.UUID, session: DBSession) -> dict:
    alert = await AlertRepository(session).get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    events: list = []
    if alert.source_ip:
        rows = await EventRepository(session).recent_for_ip(alert.source_ip, limit=50)
        events = [
            {
                "event_id": str(r.event_id),
                "timestamp": r.timestamp.isoformat(),
                "event_type": r.event_type,
                "source": r.source,
                "username": r.username,
                "status": r.status,
                "severity": r.severity,
                "message": r.message,
            }
            for r in rows
        ]
    return {"alert_id": str(alert_id), "count": len(events), "events": events}


@router.patch("/{alert_id}", response_model=AlertRead)
async def patch_alert(
    alert_id: uuid.UUID,
    body: AlertUpdate,
    session: DBSession,
    redis: RedisClient,
    principal: Principal,
    request: Request,
) -> AlertRead:
    try:
        alert = await update_alert_status(
            session,
            alert_id,
            body.status,
            actor=principal["sub"],
            note=body.note,
            request_id=request.headers.get("x-request-id"),
        )
    except InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")

    payload = AlertRead.model_validate(alert)
    await redis.publish(CHANNEL_ALERTS, payload.model_dump_json())
    return payload
