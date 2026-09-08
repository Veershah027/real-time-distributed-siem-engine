"""RULE-007 — Authentication anomaly.

Flags authentication patterns that are individually legal but collectively
unusual: a single account authenticating from many distinct source IPs in a
short window ("impossible travel" proxy), or a burst of successful logins for
an account that is normally quiet.
"""

from __future__ import annotations

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventStatus, EventType, Severity
from app.schemas.event import SecurityEvent


class AuthAnomalyDetector(Detector):
    rule_id = "RULE-007"
    name = "Authentication anomaly"
    category = "authentication"
    default_severity = Severity.MEDIUM
    kind = DetectionKind.RULE
    mitre_attack = ["T1078"]
    recommended_action = (
        "Contact the account owner to confirm the sessions. If unrecognised, "
        "invalidate active sessions, reset credentials, and review what the "
        "account accessed during the window."
    )
    default_params = {"distinct_ips": 4, "window_seconds": 300}

    def applies_to(self, event: SecurityEvent) -> bool:
        return (
            event.event_type in {EventType.AUTH_SUCCESS, EventType.AUTH_FAILURE}
            and bool(event.username)
            and bool(event.source_ip)
        )

    async def evaluate(self, event: SecurityEvent, ctx: DetectorContext) -> Detection | None:
        assert event.username and event.source_ip
        window = int(ctx.params["window_seconds"])
        threshold = int(ctx.params["distinct_ips"])

        # Track successes and failures on separate windows. A pile of failed IPs
        # against one account is password spraying (RULE-002 owns that from the
        # source side); the anomaly worth its own alert is an account that
        # *authenticates successfully* from many locations in a short window.
        bucket = "authgeo_ok" if event.status == EventStatus.SUCCESS else "authgeo_fail"
        res = await ctx.windows.add_and_measure(
            bucket,
            event.username.lower(),
            event.source_ip,
            window_seconds=window,
            now=event.timestamp.timestamp(),
        )
        if event.status != EventStatus.SUCCESS:
            return None
        distinct_ips = len(res.unique_values)
        if distinct_ips < threshold:
            return None

        confidence = min(0.92, 0.5 + 0.1 * (distinct_ips - threshold))
        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"Unusual authentication pattern for '{event.username}'",
            description=(
                f"Account '{event.username}' authenticated *successfully* from "
                f"{distinct_ips} distinct source IPs within {res.span_seconds:.0f}s "
                f"(latest from {event.source_ip}) — possible session hijack or "
                f"shared/compromised credentials."
            ),
            severity=Severity.HIGH if distinct_ips >= threshold + 2 else self.default_severity,
            confidence=round(confidence, 2),
            correlation_key=f"user:{event.username.lower()}:authgeo",
            source_ip=event.source_ip,
            affected_host=event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": f"{event.username} login from {event.source_ip} ({event.status})",
                }
            ],
            involved_users=[event.username],
            involved_hosts=[event.source],
            metadata={"distinct_source_ips": sorted(res.unique_values)[:20]},
        )
