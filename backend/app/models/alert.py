"""``alerts`` table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.schemas.enums import AlertStatus


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    detection_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="rule")

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=AlertStatus.OPEN, index=True
    )

    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    source_ip: Mapped[str | None] = mapped_column(String(45), index=True)
    affected_host: Mapped[str | None] = mapped_column(String(255))
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    involved_users: Mapped[list] = mapped_column(JSONB, default=list)
    involved_hosts: Mapped[list] = mapped_column(JSONB, default=list)
    evidence: Mapped[list] = mapped_column(JSONB, default=list)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False, default="")

    correlation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    anomaly_score: Mapped[float | None] = mapped_column(Float)
    alert_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    __table_args__ = (
        # One active correlation window per (rule, key). Terminal alerts are
        # excluded from correlation in the service layer, so a resolved brute
        # force alert does not block a fresh one from the same IP later.
        UniqueConstraint("rule_id", "correlation_key", "status", name="uq_alert_open_window"),
        Index("ix_alerts_status_sev_lastseen", "status", "severity", last_seen.desc()),
        Index("ix_alerts_lastseen_desc", last_seen.desc()),
    )
