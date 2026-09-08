"""Data-access layer. All list queries are bounded and paginated."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AuditLog, SecurityEventRow
from app.schemas.enums import AlertStatus
from app.schemas.event import SecurityEvent

MAX_LIMIT = 200


def _paginate(stmt: Select, limit: int, offset: int) -> Select:
    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)
    return stmt.limit(limit).offset(offset)


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _row_from_event(ev: SecurityEvent) -> dict[str, Any]:
        return {
            "event_id": ev.event_id,
            "timestamp": ev.timestamp,
            "ingested_at": ev.ingested_at,
            "source": ev.source,
            "source_type": ev.source_type.value,
            "event_type": ev.event_type.value,
            "source_ip": ev.source_ip,
            "destination_ip": ev.destination_ip,
            "destination_port": ev.destination_port,
            "username": ev.username,
            "service": ev.service,
            "action": ev.action,
            "status": ev.status.value if ev.status else None,
            "severity": ev.severity.value,
            "message": ev.message,
            "bytes_out": ev.bytes_out,
            "bytes_in": ev.bytes_in,
            "metadata": ev.metadata,
        }

    async def bulk_insert(self, events: list[SecurityEvent]) -> int:
        """Idempotent batch insert. Returns number of new rows."""
        if not events:
            return 0
        rows = [self._row_from_event(e) for e in events]
        stmt = (
            pg_insert(SecurityEventRow)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(SecurityEventRow.event_id)
        )
        result = await self.session.execute(stmt)
        return len(result.fetchall())

    def _filtered(
        self,
        *,
        event_type: str | None = None,
        source_ip: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        username: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        q: str | None = None,
    ) -> Select:
        stmt = select(SecurityEventRow)
        if event_type:
            stmt = stmt.where(SecurityEventRow.event_type == event_type)
        if source_ip:
            stmt = stmt.where(SecurityEventRow.source_ip == source_ip)
        if severity:
            stmt = stmt.where(SecurityEventRow.severity == severity)
        if source:
            stmt = stmt.where(SecurityEventRow.source == source)
        if username:
            stmt = stmt.where(SecurityEventRow.username == username)
        if start:
            stmt = stmt.where(SecurityEventRow.timestamp >= start)
        if end:
            stmt = stmt.where(SecurityEventRow.timestamp <= end)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(SecurityEventRow.message.ilike(like))
        return stmt

    async def list(
        self, *, limit: int = 50, offset: int = 0, **filters: Any
    ) -> tuple[list[SecurityEventRow], int]:
        base = self._filtered(**filters)
        total = await self.session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        stmt = _paginate(
            base.order_by(SecurityEventRow.timestamp.desc()), limit, offset
        )
        rows = list((await self.session.scalars(stmt)).all())
        return rows, int(total or 0)

    async def get(self, event_id: uuid.UUID) -> SecurityEventRow | None:
        return await self.session.get(SecurityEventRow, event_id)

    async def recent_for_ip(
        self, source_ip: str, limit: int = 25
    ) -> list[SecurityEventRow]:
        stmt = (
            select(SecurityEventRow)
            .where(SecurityEventRow.source_ip == source_ip)
            .order_by(SecurityEventRow.timestamp.desc())
            .limit(min(limit, MAX_LIMIT))
        )
        return list((await self.session.scalars(stmt)).all())

    async def count_since(self, since: datetime) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(SecurityEventRow)
                .where(SecurityEventRow.ingested_at >= since)
            )
            or 0
        )

    async def top_source_ips(self, since: datetime, limit: int = 10) -> list[dict[str, Any]]:
        fail_sum = func.sum(
            case((SecurityEventRow.event_type == "authentication_failure", 1), else_=0)
        )
        stmt = (
            select(
                SecurityEventRow.source_ip,
                func.count().label("events"),
                fail_sum,
            )
            .where(SecurityEventRow.timestamp >= since)
            .where(SecurityEventRow.source_ip.is_not(None))
            .group_by(SecurityEventRow.source_ip)
            .order_by(func.count().desc())
            .limit(min(limit, 50))
        )
        result = await self.session.execute(stmt)
        return [
            {"source_ip": ip, "event_count": int(cnt), "auth_failures": int(fails or 0)}
            for ip, cnt, fails in result.all()
        ]

    async def event_type_breakdown(self, since: datetime) -> list[dict[str, Any]]:
        stmt = (
            select(SecurityEventRow.event_type, func.count())
            .where(SecurityEventRow.timestamp >= since)
            .group_by(SecurityEventRow.event_type)
            .order_by(func.count().desc())
        )
        return [
            {"event_type": et, "count": int(c)}
            for et, c in (await self.session.execute(stmt)).all()
        ]

    async def timeseries(
        self, since: datetime, bucket_seconds: int = 60
    ) -> list[dict[str, Any]]:
        bucket = func.to_timestamp(
            func.floor(func.extract("epoch", SecurityEventRow.timestamp) / bucket_seconds)
            * bucket_seconds
        )
        stmt = (
            select(bucket.label("bucket"), func.count())
            .where(SecurityEventRow.timestamp >= since)
            .group_by("bucket")
            .order_by("bucket")
        )
        return [
            {"bucket": b.isoformat(), "count": int(c)}
            for b, c in (await self.session.execute(stmt)).all()
        ]


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #
class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_open_by_key(self, rule_id: str, correlation_key: str) -> Alert | None:
        stmt = select(Alert).where(
            Alert.rule_id == rule_id,
            Alert.correlation_key == correlation_key,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        )
        return await self.session.scalar(stmt)

    async def get(self, alert_id: uuid.UUID) -> Alert | None:
        return await self.session.get(Alert, alert_id)

    async def add(self, alert: Alert) -> Alert:
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def list(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        rule_id: str | None = None,
        source_ip: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Alert], int]:
        base = select(Alert)
        if status:
            base = base.where(Alert.status == status)
        if severity:
            base = base.where(Alert.severity == severity)
        if rule_id:
            base = base.where(Alert.rule_id == rule_id)
        if source_ip:
            base = base.where(Alert.source_ip == source_ip)
        total = await self.session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        stmt = _paginate(base.order_by(Alert.last_seen.desc()), limit, offset)
        rows = list((await self.session.scalars(stmt)).all())
        return rows, int(total or 0)

    async def counts_by_status_severity(self) -> dict[str, int]:
        stmt = select(Alert.status, Alert.severity, func.count()).group_by(
            Alert.status, Alert.severity
        )
        out: dict[str, int] = {}
        for st, sev, cnt in (await self.session.execute(stmt)).all():
            out[f"{st}:{sev}"] = int(cnt)
        return out

    async def timeseries(self, since: datetime, bucket_seconds: int = 300) -> list[dict[str, Any]]:
        bucket = func.to_timestamp(
            func.floor(func.extract("epoch", Alert.first_seen) / bucket_seconds) * bucket_seconds
        )
        stmt = (
            select(bucket.label("bucket"), Alert.severity, func.count())
            .where(Alert.first_seen >= since)
            .group_by("bucket", Alert.severity)
            .order_by("bucket")
        )
        return [
            {"bucket": b.isoformat(), "severity": sev, "count": int(c)}
            for b, sev, c in (await self.session.execute(stmt)).all()
        ]


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str | None = None,
        request_id: str | None = None,
        detail: dict[str, Any] | None = None,
        note: str | None = None,
    ) -> None:
        self.session.add(
            AuditLog(
                actor=actor,
                action=action,
                target_type=target_type,
                target_id=target_id,
                request_id=request_id,
                detail=detail or {},
                note=note,
            )
        )
