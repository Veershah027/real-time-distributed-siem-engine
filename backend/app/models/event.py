"""``security_events`` table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SecurityEventRow(Base):
    __tablename__ = "security_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    source: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    source_ip: Mapped[str | None] = mapped_column(String(45), index=True)
    destination_ip: Mapped[str | None] = mapped_column(String(45))
    destination_port: Mapped[int | None] = mapped_column(Integer)

    username: Mapped[str | None] = mapped_column(String(255), index=True)
    service: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    message: Mapped[str | None] = mapped_column(Text)
    bytes_out: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_in: Mapped[int] = mapped_column(BigInteger, default=0)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    __table_args__ = (
        Index("ix_events_ts_desc", timestamp.desc()),
        Index("ix_events_type_ts", "event_type", timestamp.desc()),
        Index("ix_events_srcip_ts", "source_ip", timestamp.desc()),
        Index("ix_events_severity_ts", "severity", timestamp.desc()),
    )
