"""Alert triage service — state transitions with an audit trail."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Alert
from app.schemas.enums import AlertStatus
from app.storage.repositories import AlertRepository, AuditRepository

log = get_logger("services.alerts")

# Incident workflow: OPEN -> ACKNOWLEDGED -> INVESTIGATING -> RESOLVED,
# with FALSE_POSITIVE reachable from any active state and re-open from terminal.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    AlertStatus.OPEN: {
        AlertStatus.ACKNOWLEDGED,
        AlertStatus.INVESTIGATING,
        AlertStatus.RESOLVED,
        AlertStatus.FALSE_POSITIVE,
    },
    AlertStatus.ACKNOWLEDGED: {
        AlertStatus.INVESTIGATING,
        AlertStatus.RESOLVED,
        AlertStatus.FALSE_POSITIVE,
        AlertStatus.OPEN,
    },
    AlertStatus.INVESTIGATING: {
        AlertStatus.ACKNOWLEDGED,
        AlertStatus.RESOLVED,
        AlertStatus.FALSE_POSITIVE,
        AlertStatus.OPEN,
    },
    AlertStatus.RESOLVED: {AlertStatus.OPEN},
    AlertStatus.FALSE_POSITIVE: {AlertStatus.OPEN},
}


class InvalidTransition(ValueError):
    pass


async def update_alert_status(
    session: AsyncSession,
    alert_id: uuid.UUID,
    new_status: AlertStatus,
    *,
    actor: str = "analyst",
    note: str | None = None,
    request_id: str | None = None,
) -> Alert | None:
    repo = AlertRepository(session)
    audit = AuditRepository(session)
    alert = await repo.get(alert_id)
    if alert is None:
        return None

    current = alert.status
    if current == new_status:
        return alert
    if new_status not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(f"cannot move alert from {current} to {new_status}")

    alert.status = new_status.value
    alert.updated_at = datetime.now(UTC)
    meta = dict(alert.alert_metadata)
    history = list(meta.get("status_history", []))
    history.append(
        {"from": current, "to": new_status.value, "at": alert.updated_at.isoformat(), "by": actor}
    )
    meta["status_history"] = history[-25:]
    alert.alert_metadata = meta

    await audit.record(
        actor=actor,
        action="alert_status_change",
        target_type="alert",
        target_id=str(alert_id),
        request_id=request_id,
        detail={"from": current, "to": new_status.value},
        note=note,
    )
    await session.commit()
    log.info(
        "alert_status_changed", alert_id=str(alert_id), **{"from": current, "to": new_status.value}
    )
    return alert
