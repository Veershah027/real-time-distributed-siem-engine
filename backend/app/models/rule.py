"""``detection_rules`` table — persisted catalogue + tunable thresholds."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DetectionRuleRow(Base, TimestampMixin):
    __tablename__ = "detection_rules"

    rule_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_severity: Mapped[str] = mapped_column(String(16), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mitre_attack: Mapped[list] = mapped_column(JSONB, default=list)
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False, default="")
