"""Detection-rule catalogue."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import RedisClient
from app.detection.engine import DetectionEngine

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
        "description": "Flags per-minute metrics that deviate > z-threshold σ from a rolling baseline.",
        "parameters": {},
        "mitre_attack": [],
        "recommended_action": "Investigate what changed during the flagged minute.",
    },
    {
        "rule_id": "ML-001",
        "name": "Isolation Forest outlier (optional)",
        "category": "anomaly",
        "default_severity": "medium",
        "kind": "ml",
        "enabled": False,
        "description": "Unsupervised outlier detection on per-minute feature vectors. Demo model.",
        "parameters": {},
        "mitre_attack": [],
        "recommended_action": "Confirm with deterministic rules before acting.",
    },
]


@router.get("")
async def list_detections(redis: RedisClient) -> dict:
    engine = DetectionEngine(redis)
    catalogue = engine.catalogue()
    from app.core.config import settings

    stat = list(_STATISTICAL_RULES)
    stat[1]["enabled"] = settings.enable_ml
    return {"rules": catalogue + stat, "count": len(catalogue) + len(stat)}


@router.get("/{rule_id}")
async def get_detection(rule_id: str, redis: RedisClient) -> dict:
    engine = DetectionEngine(redis)
    for entry in engine.catalogue() + _STATISTICAL_RULES:
        if entry["rule_id"].lower() == rule_id.lower():
            return entry
    raise HTTPException(status_code=404, detail="rule not found")
