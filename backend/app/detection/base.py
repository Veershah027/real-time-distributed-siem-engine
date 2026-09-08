"""Detector interface and result types.

Every detector — rule-based or statistical — implements the same small
protocol so the engine can treat them uniformly.  Detectors are *stateless*
objects; all cross-event state lives in Redis (sliding windows) so the engine
scales horizontally across worker processes.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.schemas.enums import DetectionKind, Severity
from app.schemas.event import SecurityEvent

if TYPE_CHECKING:
    from app.detection.windows import WindowStore


@dataclass(slots=True)
class Detection:
    """A single detector firing on an event."""

    rule_id: str
    kind: DetectionKind
    title: str
    description: str
    severity: Severity
    confidence: float
    correlation_key: str
    source_ip: str | None
    affected_host: str | None
    recommended_action: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    involved_users: list[str] = field(default_factory=list)
    involved_hosts: list[str] = field(default_factory=list)
    event_count_hint: int = 1
    anomaly_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    triggered_at: datetime | None = None


@dataclass(slots=True)
class DetectorContext:
    """Everything a detector needs beyond the event itself."""

    windows: WindowStore
    params: dict[str, Any]


class Detector(abc.ABC):
    rule_id: str
    name: str
    category: str
    default_severity: Severity
    kind: DetectionKind = DetectionKind.RULE
    mitre_attack: list[str] = []
    recommended_action: str = ""

    #: default tunable parameters; overridden by config / DB
    default_params: dict[str, Any] = {}

    def applies_to(self, event: SecurityEvent) -> bool:  # cheap pre-filter
        return True

    @abc.abstractmethod
    async def evaluate(
        self, event: SecurityEvent, ctx: DetectorContext
    ) -> Detection | None: ...

    def catalogue_entry(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "category": self.category,
            "default_severity": self.default_severity.value,
            "kind": self.kind.value,
            "mitre_attack": self.mitre_attack,
            "parameters": {**self.default_params, **self.default_params},
            "recommended_action": self.recommended_action,
        }
