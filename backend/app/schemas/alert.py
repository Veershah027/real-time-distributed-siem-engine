"""Alert schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AlertStatus, DetectionKind, Severity


class AlertEvidence(BaseModel):
    """A compact reference to an event that contributed to an alert."""

    event_id: uuid.UUID
    timestamp: datetime
    summary: str


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: uuid.UUID
    rule_id: str
    detection_kind: DetectionKind
    title: str
    description: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    status: AlertStatus
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    source_ip: str | None
    affected_host: str | None
    event_count: int
    involved_users: list[str]
    involved_hosts: list[str]
    evidence: list[dict[str, Any]]
    recommended_action: str
    correlation_key: str
    anomaly_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertUpdate(BaseModel):
    """PATCH body for alert triage."""

    status: AlertStatus
    note: str | None = Field(None, max_length=1000)


class AlertListResponse(BaseModel):
    items: list[AlertRead]
    total: int
    limit: int
    offset: int
