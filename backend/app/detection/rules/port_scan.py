"""RULE-003 — Port scanning (one source IP, many unique destination ports)."""

from __future__ import annotations

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventType, Severity
from app.schemas.event import SecurityEvent

_SCAN_EVENTS = {
    EventType.CONNECTION_ATTEMPT,
    EventType.FIREWALL_DENY,
    EventType.FIREWALL_ALLOW,
    EventType.NETWORK_FLOW,
}


class PortScanDetector(Detector):
    rule_id = "RULE-003"
    name = "Port scanning"
    category = "network"
    default_severity = Severity.HIGH
    kind = DetectionKind.RULE
    mitre_attack = ["T1046"]
    recommended_action = (
        "Treat the source as reconnaissance. Block at the perimeter, check whether "
        "any probed service responded, and review exposure of the scanned ports."
    )
    default_params = {"unique_ports": 20, "window_seconds": 30}

    def applies_to(self, event: SecurityEvent) -> bool:
        return (
            event.event_type in _SCAN_EVENTS
            and event.source_ip is not None
            and event.destination_port is not None
        )

    async def evaluate(self, event: SecurityEvent, ctx: DetectorContext) -> Detection | None:
        assert event.source_ip is not None and event.destination_port is not None
        window = int(ctx.params["window_seconds"])
        threshold = int(ctx.params["unique_ports"])

        res = await ctx.windows.add_and_measure(
            "portscan",
            event.source_ip,
            str(event.destination_port),
            window_seconds=window,
            now=event.timestamp.timestamp(),
        )
        unique_ports = len(res.unique_values)
        if unique_ports < threshold:
            return None

        rate = unique_ports / max(res.span_seconds, 1.0)
        confidence = min(0.98, 0.6 + 0.015 * (unique_ports - threshold))
        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"Port scan from {event.source_ip}",
            description=(
                f"{event.source_ip} contacted {unique_ports} unique destination ports "
                f"in {res.span_seconds:.0f}s (~{rate:.1f} ports/s, threshold "
                f"{threshold}/{window}s)."
            ),
            severity=self.default_severity,
            confidence=round(confidence, 2),
            correlation_key=f"srcip:{event.source_ip}:portscan",
            source_ip=event.source_ip,
            affected_host=event.destination_ip or event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": (
                        f"{event.event_type.value} -> {event.destination_ip}:"
                        f"{event.destination_port}"
                    ),
                }
            ],
            involved_hosts=[event.destination_ip] if event.destination_ip else [],
            event_count_hint=res.count,
            metadata={
                "unique_ports": unique_ports,
                "ports_sample": sorted(int(p) for p in list(res.unique_values)[:30] if p.isdigit()),
                "window_seconds": window,
            },
        )
