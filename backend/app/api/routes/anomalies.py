"""Statistical anomaly view — recent anomaly alerts + current baselines.

All numbers come from the running EWMA anomaly engine; nothing is synthesised.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DBSession, RedisClient
from app.detection.anomaly import StatisticalAnomalyDetector
from app.storage.repositories import AlertRepository

router = APIRouter()

_METRICS = (
    "events_per_min",
    "auth_failures_per_min",
    "unique_source_ips",
    "outbound_mib_per_min",
    "db_errors_per_min",
    "firewall_denies_per_min",
)


def _deviation_pct(current: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return round((current - baseline) / baseline * 100, 1)


@router.get("")
async def list_anomalies(
    session: DBSession,
    redis: RedisClient,
    limit: int = Query(30, ge=1, le=200),
) -> dict:
    repo = AlertRepository(session)
    alerts = await repo.recent_by_kind("anomaly", limit) + await repo.recent_by_kind("ml", limit)
    alerts.sort(key=lambda a: a.last_seen, reverse=True)

    items = []
    for a in alerts[:limit]:
        meta = a.alert_metadata or {}
        current = float(meta.get("value", 0) or 0)
        base_mean = float(meta.get("baseline_mean", 0) or 0)
        items.append(
            {
                "alert_id": str(a.alert_id),
                "rule_id": a.rule_id,
                "metric": meta.get("metric"),
                "current_value": current,
                "baseline_mean": base_mean,
                "baseline_std": float(meta.get("baseline_std", 0) or 0),
                "z_score": float(meta.get("z_score", 0) or 0),
                "deviation_pct": _deviation_pct(current, base_mean),
                "severity": a.severity,
                "confidence": a.confidence,
                "anomaly_score": a.anomaly_score,
                "status": a.status,
                "first_seen": a.first_seen.isoformat(),
                "last_seen": a.last_seen.isoformat(),
                "description": a.description,
                "source_ip": a.source_ip,
            }
        )

    detector = StatisticalAnomalyDetector(redis)
    baselines = []
    for metric in _METRICS:
        b = await detector.baseline(metric)
        baselines.append(
            {
                "metric": metric,
                "mean": round(b["mean"], 2),
                "std": round(b["std"], 2),
                "samples": int(b["n"]),
                "ready": int(b["n"]) >= detector.min_samples,
            }
        )

    return {
        "z_score_threshold": detector.z_threshold,
        "min_samples": detector.min_samples,
        "anomalies": items,
        "baselines": baselines,
    }
