"""Detection-rule catalogue with live trigger activity."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import DBSession, RedisClient
from app.core.config import settings
from app.detection.engine import DetectionEngine
from app.storage.repositories import AlertRepository

router = APIRouter()

# Anomaly / ML pseudo-rules surfaced in the catalogue for the dashboard.
_STATISTICAL_RULES = [
    {
        "rule_id": "ANOM-001",
        "name": "Statistical traffic anomaly (EWMA z-score)",
        "category": "anomaly",
        "default_severity": "medium",
        "kind": "anomaly",
        "enabled": True,
        "description": (
            "Flags per-minute metrics that deviate beyond the configured z-score "
            "from a rolling exponentially-weighted baseline."
        ),
        "parameters": {
            "zscore_threshold": settings.anomaly_zscore_threshold,
            "ewma_alpha": settings.anomaly_ewma_alpha,
            "min_samples": settings.anomaly_min_samples,
        },
        "mitre_attack": [],
        "recommended_action": "Investigate what changed in the environment during the flagged minute.",
    },
    {
        "rule_id": "ML-001",
        "name": "Isolation Forest outlier (optional)",
        "category": "anomaly",
        "default_severity": "medium",
        "kind": "ml",
        "enabled": settings.enable_ml,
        "description": (
            "Unsupervised outlier detection on per-minute feature vectors. "
            "Research/demo model; never overrides a deterministic rule."
        ),
        "parameters": {},
        "mitre_attack": [],
        "recommended_action": "Confirm with deterministic rules before acting.",
    },
]


def _slug(rule_id: str) -> str:
    """RULE-001 -> SSH_BRUTE_FORCE style handle for the rules page."""
    return {
        "RULE-001": "SSH_BRUTE_FORCE",
        "RULE-002": "PASSWORD_SPRAY",
        "RULE-003": "PORT_SCAN",
        "RULE-004": "PRIVILEGE_ESCALATION",
        "RULE-005": "SUSPICIOUS_SQL",
        "RULE-006": "DATA_EXFILTRATION",
        "RULE-007": "AUTH_ANOMALY",
        "ANOM-001": "TRAFFIC_ANOMALY",
        "ML-001": "ISOLATION_FOREST",
    }.get(rule_id, rule_id.replace("-", "_"))


async def _catalogue_with_activity(session: DBSession, redis: RedisClient) -> list[dict]:
    engine = DetectionEngine(redis)
    activity = await AlertRepository(session).rule_activity()
    out: list[dict] = []
    for entry in [*engine.catalogue(), *_STATISTICAL_RULES]:
        act = activity.get(entry["rule_id"], {})
        out.append(
            {
                **entry,
                "handle": _slug(entry["rule_id"]),
                "trigger_count": act.get("trigger_count", 0),
                "active_count": act.get("active_count", 0),
                "last_triggered": act.get("last_triggered"),
            }
        )
    return out


@router.get("")
async def list_detections(session: DBSession, redis: RedisClient) -> dict:
    rules = await _catalogue_with_activity(session, redis)
    return {
        "rules": rules,
        "count": len(rules),
        "total_triggers": sum(r["trigger_count"] for r in rules),
    }


@router.get("/{rule_id}")
async def get_detection(rule_id: str, session: DBSession, redis: RedisClient) -> dict:
    rules = await _catalogue_with_activity(session, redis)
    for entry in rules:
        if (
            entry["rule_id"].lower() == rule_id.lower()
            or entry["handle"].lower() == rule_id.lower()
        ):
            return entry
    raise HTTPException(status_code=404, detail="rule not found")
