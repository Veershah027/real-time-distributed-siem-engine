"""``hosts`` table — inventory of sources seen by the SIEM."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Host(Base, TimestampMixin):
    __tablename__ = "hosts"

    hostname: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    alert_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
