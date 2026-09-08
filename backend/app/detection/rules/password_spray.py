"""RULE-002 — Password spraying (one source IP, many distinct usernames)."""

from __future__ import annotations

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventType, Severity
from app.schemas.event import SecurityEvent


class PasswordSprayDetector(Detector):
    rule_id = "RULE-002"
    name = "Password spraying"
    category = "authentication"
    default_severity = Severity.HIGH
    kind = DetectionKind.RULE
    mitre_attack = ["T1110.003"]
    recommended_action = (
        "Confirm whether the source IP is a legitimate gateway (VPN/NAT). If not, "
        "block it and review accounts targeted for weak-password exposure; enable "
        "MFA where missing."
    )
    default_params = {"unique_users": 8, "window_seconds": 120}

    def applies_to(self, event: SecurityEvent) -> bool:
        return event.event_type == EventType.AUTH_FAILURE and bool(
            event.source_ip and event.username
        )

    async def evaluate(self, event: SecurityEvent, ctx: DetectorContext) -> Detection | None:
        assert event.source_ip is not None
        window = int(ctx.params["window_seconds"])
        threshold = int(ctx.params["unique_users"])

        res = await ctx.windows.add_and_measure(
            "spray",
            event.source_ip,
            (event.username or "-").lower(),
            window_seconds=window,
            now=event.timestamp.timestamp(),
        )
        distinct = len({u for u in res.unique_values if u and u != "-"})
        if distinct < threshold:
            return None

        confidence = min(0.97, 0.55 + 0.03 * (distinct - threshold))
        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"Password spraying from {event.source_ip}",
            description=(
                f"{event.source_ip} attempted authentication against {distinct} distinct "
                f"usernames in {res.span_seconds:.0f}s ({res.count} attempts total), "
                f"a low-and-slow pattern consistent with password spraying."
            ),
            severity=self.default_severity,
            confidence=round(confidence, 2),
            correlation_key=f"srcip:{event.source_ip}:spray",
            source_ip=event.source_ip,
            affected_host=event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": f"auth failure user={event.username} host={event.source}",
                }
            ],
            involved_users=sorted(u for u in res.unique_values if u and u != "-")[:25],
            involved_hosts=[event.source],
            event_count_hint=res.count,
            metadata={"distinct_users": distinct, "window_seconds": window},
        )
