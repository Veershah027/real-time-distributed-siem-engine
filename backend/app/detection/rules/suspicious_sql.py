"""RULE-005 — Suspicious database activity (synthetic SQL patterns).

Operates on synthetic ``db_query`` events only. It never executes SQL; it
pattern-matches the query text carried in the event for classic injection and
exfiltration tells.
"""

from __future__ import annotations

import re

from app.detection.base import Detection, Detector, DetectorContext
from app.schemas.enums import DetectionKind, EventType, Severity
from app.schemas.event import SecurityEvent

_PATTERNS: list[tuple[str, str, float]] = [
    (r"(?i)\bunion\s+select\b", "UNION-based injection", 0.9),
    (r"(?i)\bor\s+1\s*=\s*1\b", "tautology injection (OR 1=1)", 0.85),
    (r"(?i)';\s*(drop|delete|update|insert)\b", "stacked-query injection", 0.9),
    (r"(?i)\b(information_schema|pg_catalog|sysobjects)\b", "schema enumeration", 0.6),
    (r"(?i)\b(load_file|into\s+outfile|pg_read_file|xp_cmdshell)\b", "file / command access", 0.95),
    (r"(?i)\bselect\b.{0,40}\bfrom\b.{0,40}\b(users|credentials|customers|payment)\b.*", "bulk read of sensitive table", 0.5),
    (r"(?i)--\s*$", "inline comment truncation", 0.4),
    (r"(?i)\bsleep\s*\(\s*\d+\s*\)|\bwaitfor\s+delay\b", "time-based blind injection", 0.85),
]
_COMPILED = [(re.compile(p), label, w) for p, label, w in _PATTERNS]
_LARGE_ROWCOUNT = 5000


class SuspiciousSQLDetector(Detector):
    rule_id = "RULE-005"
    name = "Suspicious database activity"
    category = "database"
    default_severity = Severity.MEDIUM
    kind = DetectionKind.RULE
    mitre_attack = ["T1190", "T1213"]
    recommended_action = (
        "Correlate with the calling application and user. Review DB audit logs "
        "for the session, confirm parameterised queries in the code path, and "
        "check for unexpected data volume leaving the database."
    )
    default_params = {"large_rowcount": _LARGE_ROWCOUNT}

    def applies_to(self, event: SecurityEvent) -> bool:
        return event.event_type in {EventType.DB_QUERY, EventType.DB_ERROR}

    async def evaluate(
        self, event: SecurityEvent, ctx: DetectorContext
    ) -> Detection | None:
        query = str(event.metadata.get("query") or event.message or "")
        if not query:
            return None

        hits: list[str] = []
        score = 0.0
        for rx, label, weight in _COMPILED:
            if rx.search(query):
                hits.append(label)
                score = max(score, weight)

        rows = int(event.metadata.get("rows_returned") or 0)
        big_read = rows >= int(ctx.params["large_rowcount"])
        if big_read:
            hits.append(f"large result set ({rows} rows)")
            score = max(score, 0.55)

        if not hits:
            return None

        severity = Severity.HIGH if score >= 0.85 else Severity.MEDIUM
        return Detection(
            rule_id=self.rule_id,
            kind=self.kind,
            title=f"Suspicious SQL from {event.username or event.source_ip or 'unknown'}",
            description=(
                f"Query on {event.source} matched: {', '.join(hits)}. "
                f"Query (truncated): {query[:200]}"
            ),
            severity=severity,
            confidence=round(min(0.96, score), 2),
            correlation_key=f"db:{event.source}:user:{event.username or event.source_ip}:sqli",
            source_ip=event.source_ip,
            affected_host=event.source,
            recommended_action=self.recommended_action,
            evidence=[
                {
                    "event_id": str(event.event_id),
                    "timestamp": event.timestamp.isoformat(),
                    "summary": f"{event.username or '?'} @ {event.source}: {query[:120]}",
                }
            ],
            involved_users=[event.username] if event.username else [],
            involved_hosts=[event.source],
            metadata={"patterns": hits, "rows_returned": rows},
        )
