"""RULE-004 — Suspicious privilege escalation."""

from __future__ import annotations

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventType, Severity
from app.schemas.event import SecurityEvent

_SUSPICIOUS_ACTIONS = (
    "sudo",
    "su ",
    "usermod",
    "useradd",
    "passwd",
    "chmod 777",
    "setuid",
    "visudo",
    "pkexec",
    "runas",
    "net localgroup administrators",
)
_OFF_HOURS = set(range(22, 24)) | set(range(0, 6))  # 22:00–05:59 UTC


class PrivilegeEscalationDetector(Detector):
    rule_id = "RULE-004"
    name = "Privilege escalation"
    category = "authentication"
    default_severity = Severity.HIGH
    kind = DetectionKind.RULE
    mitre_attack = ["T1548", "T1078"]
    recommended_action = (
        "Verify the change with the account owner and change-management records. "
        "If unsanctioned, revoke the elevated access, preserve the host for "
        "forensics, and rotate credentials."
    )
    default_params = {"privileged_roles": ["admin", "root", "sudo", "administrator"]}

    def applies_to(self, event: SecurityEvent) -> bool:
        return event.event_type in {
            EventType.PRIVILEGE_ESCALATION,
            EventType.CONFIG_CHANGE,
            EventType.APP_EVENT,
        } or bool(event.action and any(s in event.action.lower() for s in _SUSPICIOUS_ACTIONS))

    async def evaluate(self, event: SecurityEvent, ctx: DetectorContext) -> Detection | None:
        action = (event.action or event.message or "").lower()
        is_priv_action = event.event_type == EventType.PRIVILEGE_ESCALATION or any(
            s in action for s in _SUSPICIOUS_ACTIONS
        )
        if not is_priv_action:
            return None

        roles = {r.lower() for r in ctx.params.get("privileged_roles", [])}
        actor_role = str(event.metadata.get("user_role", "")).lower()
        actor_is_privileged = actor_role in roles or (event.username or "").lower() in roles

        # A normal (non-privileged) user performing an admin action is the signal.
        low_priv_actor = not actor_is_privileged

        off_hours = event.timestamp.hour in _OFF_HOURS
        explicit_flag = event.event_type == EventType.PRIVILEGE_ESCALATION

        if not (low_priv_actor or off_hours or explicit_flag):
            return None

        score = 0.4
        reasons = []
        if low_priv_actor:
            score += 0.35
            reasons.append(f"actor '{event.username}' is not a known privileged account")
        if off_hours:
            score += 0.15
            reasons.append("action occurred outside business hours")
        if explicit_flag:
            score += 0.2
            reasons.append("host reported an explicit privilege-escalation event")
        if str(event.status) == "failure":
            score += 0.05
            reasons.append("the escalation attempt failed")

        confidence = min(0.95, score)
        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"Privilege escalation by {event.username or 'unknown'} on {event.source}",
            description=(
                f"User '{event.username}' performed administrative action "
                f"'{event.action or action[:120]}' on {event.source}. "
                + "; ".join(reasons).capitalize()
                + "."
            ),
            severity=self.default_severity,
            confidence=round(confidence, 2),
            correlation_key=f"host:{event.source}:user:{event.username}:privesc",
            source_ip=event.source_ip,
            affected_host=event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": f"{event.username}@{event.source}: {event.action or action[:80]}",
                }
            ],
            involved_users=[event.username] if event.username else [],
            involved_hosts=[event.source],
            metadata={"reasons": reasons, "actor_role": actor_role or "unknown"},
        )
