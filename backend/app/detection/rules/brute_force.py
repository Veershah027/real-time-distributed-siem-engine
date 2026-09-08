"""RULE-001 — SSH / service brute force."""

from __future__ import annotations

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventType, Severity
from app.schemas.event import SecurityEvent


class BruteForceDetector(Detector):
    rule_id = "RULE-001"
    name = "SSH/Service brute force"
    category = "authentication"
    default_severity = Severity.HIGH
    kind = DetectionKind.RULE
    mitre_attack = ["T1110.001"]
    recommended_action = (
        "Investigate the source IP. If not attributable to a known scanner or "
        "user, block it at the firewall and force a credential reset for any "
        "account that authenticated successfully from it."
    )
    default_params = {"max_failures": 10, "window_seconds": 60}

    def applies_to(self, event: SecurityEvent) -> bool:
        return (
            event.event_type == EventType.AUTH_FAILURE
            or (event.event_type == EventType.AUTH_SUCCESS and event.source_ip is not None)
        ) and event.source_ip is not None

    async def evaluate(self, event: SecurityEvent, ctx: DetectorContext) -> Detection | None:
        assert event.source_ip is not None
        window = int(ctx.params["window_seconds"])
        threshold = int(ctx.params["max_failures"])

        if event.event_type == EventType.AUTH_SUCCESS:
            # A success from an IP mid-spree raises confidence but does not by
            # itself trigger; measure without adding.
            res = await ctx.windows.measure("bruteforce", event.source_ip, window_seconds=window)
            if res.count < threshold:
                return None
            breached_account = True
        else:
            res = await ctx.windows.add_and_measure(
                "bruteforce",
                event.source_ip,
                event.username or "-",
                window_seconds=window,
                now=event.timestamp.timestamp(),
            )
            breached_account = False
            if res.count < threshold:
                return None

        confidence = min(0.99, 0.6 + 0.02 * (res.count - threshold))
        if breached_account:
            confidence = min(0.99, confidence + 0.15)

        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"Brute-force login activity from {event.source_ip}",
            description=(
                f"{res.count} failed authentication attempts from {event.source_ip} "
                f"within {res.span_seconds:.0f}s (threshold {threshold}/{window}s), "
                f"targeting {len(res.unique_values)} distinct account(s)."
                + (" A subsequent successful login was observed." if breached_account else "")
            ),
            severity=Severity.CRITICAL if breached_account else self.default_severity,
            confidence=round(confidence, 2),
            correlation_key=f"srcip:{event.source_ip}",
            source_ip=event.source_ip,
            affected_host=event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": f"{event.event_type.value} user={event.username} host={event.source}",
                }
            ],
            involved_users=sorted(v for v in res.unique_values if v and v != "-"),
            involved_hosts=[event.source],
            event_count_hint=res.count,
            metadata={
                "window_seconds": window,
                "span_seconds": round(res.span_seconds, 1),
                "account_breached": breached_account,
                "status": event.status.value if event.status else None,
            },
        )
