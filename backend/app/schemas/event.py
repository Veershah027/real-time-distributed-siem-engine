"""Security event schemas.

``RawEvent`` is the permissive shape accepted off the wire from producers.
``SecurityEvent`` is the strongly-typed, normalized internal representation that
the detection engine and storage layer operate on.  Producer-supplied fields are
never trusted blindly: types are coerced, IPs validated, timestamps normalized to
UTC, strings length-bounded, and unknown enum values funnelled to ``unknown``.
"""

from __future__ import annotations

import ipaddress
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.schemas.enums import EventStatus, EventType, Severity, SourceType

_MAX_STR = 512
_MAX_MSG = 2048


def _clip(value: str | None, limit: int = _MAX_STR) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value[:limit] if value else None


def _coerce_ip(value: Any) -> str | None:
    if value in (None, "", "-"):
        return None
    try:
        return str(ipaddress.ip_address(str(value).strip()))
    except ValueError:
        return None


class RawEvent(BaseModel):
    """Loosely-validated event as delivered by a producer / simulator."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    event_id: str | None = None
    timestamp: Any = None
    source: str | None = None
    source_type: str | None = None
    event_type: str | None = None
    source_ip: Any = None
    destination_ip: Any = None
    destination_port: Any = None
    username: str | None = None
    service: str | None = None
    action: str | None = None
    status: str | None = None
    severity: str | None = None
    message: str | None = None
    bytes_out: Any = None
    bytes_in: Any = None
    metadata: dict[str, Any] | None = None


class SecurityEvent(BaseModel):
    """Normalized internal event. Immutable once constructed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = "unknown"
    source_type: SourceType = SourceType.UNKNOWN
    event_type: EventType = EventType.UNKNOWN
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = None
    username: str | None = None
    service: str | None = None
    action: str | None = None
    status: EventStatus | None = None
    severity: Severity = Severity.INFO
    message: str | None = None
    bytes_out: int = 0
    bytes_in: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------ #
    @field_validator("timestamp", "ingested_at", mode="before")
    @classmethod
    def _normalize_ts(cls, value: Any) -> datetime:
        if value is None:
            return datetime.now(UTC)
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, int | float):
            dt = datetime.fromtimestamp(float(value), tz=UTC)
        else:
            raw = str(value).strip().replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(raw)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError(f"unparseable timestamp: {value!r}") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(UTC)
        # Reject absurd clock skew (> 1 day in the future) — clamp to now.
        now = datetime.now(UTC)
        if (dt - now).total_seconds() > 86_400:
            return now
        return dt

    @field_validator("source_ip", "destination_ip", mode="before")
    @classmethod
    def _validate_ip(cls, value: Any) -> str | None:
        return _coerce_ip(value)

    @field_validator("destination_port", mode="before")
    @classmethod
    def _validate_port(cls, value: Any) -> int | None:
        if value in (None, "", "-"):
            return None
        try:
            port = int(value)
        except (TypeError, ValueError):
            return None
        return port if 0 <= port <= 65535 else None

    @field_validator("bytes_out", "bytes_in", mode="before")
    @classmethod
    def _validate_bytes(cls, value: Any) -> int:
        try:
            n = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, min(n, 2**63 - 1))

    @field_validator("source", mode="before")
    @classmethod
    def _clip_source(cls, value: Any) -> str:
        return _clip(str(value)) or "unknown" if value is not None else "unknown"

    @field_validator("username", "service", "action", mode="before")
    @classmethod
    def _clip_short(cls, value: Any) -> str | None:
        return _clip(str(value)) if value is not None else None

    @field_validator("message", mode="before")
    @classmethod
    def _clip_message(cls, value: Any) -> str | None:
        return _clip(str(value), _MAX_MSG) if value is not None else None

    @field_validator("source_type", mode="before")
    @classmethod
    def _coerce_source_type(cls, value: Any) -> SourceType:
        try:
            return SourceType(str(value).lower())
        except ValueError:
            return SourceType.UNKNOWN

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> EventType:
        try:
            return EventType(str(value).lower())
        except ValueError:
            return EventType.UNKNOWN

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value: Any) -> EventStatus | None:
        if value is None:
            return None
        try:
            return EventStatus(str(value).lower())
        except ValueError:
            return EventStatus.INFO

    @field_validator("severity", mode="before")
    @classmethod
    def _coerce_severity(cls, value: Any, info: ValidationInfo) -> Severity:
        if value is None:
            return Severity.INFO
        try:
            return Severity(str(value).lower())
        except ValueError:
            return Severity.INFO

    @field_validator("metadata", mode="before")
    @classmethod
    def _bound_metadata(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        # cap size to avoid a hostile producer bloating storage
        items = list(value.items())[:50]
        return {str(k)[:128]: v for k, v in items}

    @model_validator(mode="after")
    def _derive_event_id(self) -> SecurityEvent:
        return self

    # ------------------------------------------------------------------ #
    @classmethod
    def from_raw(cls, raw: RawEvent | dict[str, Any]) -> SecurityEvent:
        """Build a normalized event from a raw producer payload."""
        data = raw.model_dump() if isinstance(raw, RawEvent) else dict(raw)
        # Pull known extras that RawEvent.extra captured
        extra = {
            k: v for k, v in data.items() if k not in cls.model_fields and k not in {"metadata"}
        }
        raw_meta = data.get("metadata")
        meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
        for k, v in extra.items():
            meta.setdefault(k, v)

        eid = data.get("event_id")
        try:
            event_id = uuid.UUID(str(eid)) if eid else uuid.uuid4()
        except ValueError:
            event_id = uuid.uuid5(uuid.NAMESPACE_URL, str(eid))

        return cls(
            event_id=event_id,
            timestamp=data.get("timestamp"),
            source=data.get("source"),
            source_type=data.get("source_type"),
            event_type=data.get("event_type"),
            source_ip=data.get("source_ip"),
            destination_ip=data.get("destination_ip"),
            destination_port=data.get("destination_port"),
            username=data.get("username"),
            service=data.get("service"),
            action=data.get("action"),
            status=data.get("status"),
            severity=data.get("severity"),
            message=data.get("message"),
            bytes_out=data.get("bytes_out", 0),
            bytes_in=data.get("bytes_in", 0),
            metadata=meta,
        )


class EventRead(BaseModel):
    """API response shape for a stored event."""

    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    timestamp: datetime
    ingested_at: datetime
    source: str
    source_type: str
    event_type: str
    source_ip: str | None
    destination_ip: str | None
    destination_port: int | None
    username: str | None
    service: str | None
    action: str | None
    status: str | None
    severity: str
    message: str | None
    bytes_out: int
    bytes_in: int
    metadata: dict[str, Any]
