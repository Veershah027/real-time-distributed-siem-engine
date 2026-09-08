"""RULE-006 — Excessive outbound data volume (possible exfiltration)."""

from __future__ import annotations

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventType, Severity
from app.schemas.event import SecurityEvent

_FLOW_EVENTS = {EventType.NETWORK_FLOW, EventType.FIREWALL_ALLOW, EventType.HTTP_REQUEST}


def _human_bytes(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} PiB"


class DataExfiltrationDetector(Detector):
    rule_id = "RULE-006"
    name = "Excessive outbound traffic"
    category = "network"
    default_severity = Severity.MEDIUM
    kind = DetectionKind.RULE
    mitre_attack = ["T1041", "T1048"]
    recommended_action = (
        "Identify the destination and whether it is an approved endpoint. If not, "
        "isolate the host, capture the flow for analysis, and check for staging "
        "of archives on the source host."
    )
    default_params = {"bytes_threshold": 52_428_800, "window_seconds": 60}

    def applies_to(self, event: SecurityEvent) -> bool:
        return event.event_type in _FLOW_EVENTS and event.bytes_out > 0 and bool(event.source_ip)

    async def evaluate(
        self, event: SecurityEvent, ctx: DetectorContext
    ) -> Detection | None:
        assert event.source_ip is not None
        window = int(ctx.params["window_seconds"])
        threshold = int(ctx.params["bytes_threshold"])

        entity = f"{event.source_ip}->{event.destination_ip or 'any'}"
        total = await ctx.windows.incr_sum(
            "exfil",
            entity,
            event.bytes_out,
            window_seconds=window,
            now=event.timestamp.timestamp(),
        )
        if total < threshold:
            return None

        ratio = total / threshold
        severity = Severity.HIGH if ratio >= 3 else Severity.MEDIUM
        confidence = min(0.95, 0.5 + 0.1 * ratio)
        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"High outbound volume from {event.source_ip}",
            description=(
                f"{_human_bytes(total)} transferred from {event.source_ip} to "
                f"{event.destination_ip or 'multiple destinations'} within {window}s "
                f"(threshold {_human_bytes(threshold)})."
            ),
            severity=severity,
            confidence=round(confidence, 2),
            correlation_key=f"srcip:{event.source_ip}:exfil",
            source_ip=event.source_ip,
            affected_host=event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": (
                        f"{_human_bytes(event.bytes_out)} -> {event.destination_ip}:"
                        f"{event.destination_port}"
                    ),
                }
            ],
            involved_hosts=[event.destination_ip] if event.destination_ip else [],
            metadata={
                "window_bytes": total,
                "window_seconds": window,
                "destination": event.destination_ip,
            },
        )
