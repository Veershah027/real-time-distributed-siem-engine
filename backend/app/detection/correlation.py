"""Alert correlation / de-duplication.

A detector fires once per contributing event.  The correlator folds those
firings into a single alert per ``(rule_id, correlation_key)`` while an alert
for that key is still in a non-terminal state.  27 SSH failures from one IP
therefore produce ONE alert with ``event_count = 27`` — not 27 alerts.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.logging import get_logger
from app.detection.base import Detection
from app.models import Alert
from app.schemas.enums import AlertStatus, Severity
from app.storage.repositories import AlertRepository

log = get_logger("detection.correlation")

_MAX_EVIDENCE = 25
_MAX_INVOLVED = 50


class AlertCorrelator:
    def __init__(self, alert_repo: AlertRepository) -> None:
        self.repo = alert_repo

    async def apply(self, detection: Detection) -> tuple[Alert, bool]:
        """Returns (alert, created)."""
        now = detection.triggered_at or datetime.now(UTC)
        existing = await self.repo.get_open_by_key(detection.rule_id, detection.correlation_key)

        if existing is None:
            alert = Alert(
                rule_id=detection.rule_id,
                detection_kind=detection.kind.value,
                title=detection.title,
                description=detection.description,
                severity=detection.severity.value,
                confidence=detection.confidence,
                status=AlertStatus.OPEN.value,
                first_seen=now,
                last_seen=now,
                source_ip=detection.source_ip,
                affected_host=detection.affected_host,
                event_count=max(1, detection.event_count_hint),
                involved_users=detection.involved_users[:_MAX_INVOLVED],
                involved_hosts=detection.involved_hosts[:_MAX_INVOLVED],
                evidence=detection.evidence[:_MAX_EVIDENCE],
                recommended_action=detection.recommended_action,
                correlation_key=detection.correlation_key,
                anomaly_score=detection.anomaly_score,
                alert_metadata=detection.metadata,
                # set explicitly so the just-flushed object is fully populated
                # without a refresh round trip (server_default would otherwise
                # leave these unloaded for the in-memory instance)
                created_at=now,
                updated_at=now,
            )
            await self.repo.add(alert)
            log.info(
                "alert_created",
                alert_id=str(alert.alert_id),
                rule_id=alert.rule_id,
                severity=alert.severity,
                correlation_key=alert.correlation_key,
            )
            return alert, True

        # --- fold into the existing alert ---
        existing.last_seen = now
        existing.event_count = max(existing.event_count + 1, detection.event_count_hint)
        existing.confidence = max(existing.confidence, detection.confidence)
        if Severity(detection.severity).rank > Severity(existing.severity).rank:
            existing.severity = detection.severity.value
            existing.title = detection.title
            existing.description = detection.description

        existing.involved_users = sorted(
            set(existing.involved_users) | set(detection.involved_users)
        )[:_MAX_INVOLVED]
        existing.involved_hosts = sorted(
            set(existing.involved_hosts) | {h for h in detection.involved_hosts if h}
        )[:_MAX_INVOLVED]

        evidence = list(existing.evidence)
        for item in detection.evidence:
            if item not in evidence:
                evidence.append(item)
        existing.evidence = evidence[-_MAX_EVIDENCE:]

        merged_meta = dict(existing.alert_metadata)
        merged_meta.update(detection.metadata)
        existing.alert_metadata = merged_meta
        if detection.anomaly_score is not None:
            existing.anomaly_score = max(existing.anomaly_score or 0.0, detection.anomaly_score)

        log.debug(
            "alert_correlated",
            alert_id=str(existing.alert_id),
            rule_id=existing.rule_id,
            event_count=existing.event_count,
        )
        return existing, False
