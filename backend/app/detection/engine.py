"""Detection engine — orchestrates all rule detectors for a single event."""

from __future__ import annotations

import time
from datetime import UTC, datetime

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import DETECTION_LATENCY
from app.detection.base import Detection, Detector, DetectorContext
from app.detection.rules import RULE_DETECTORS
from app.detection.windows import WindowStore
from app.schemas.event import SecurityEvent

log = get_logger("detection.engine")


def _resolve_params(detector: Detector) -> dict:
    """Merge detector defaults with env-configured overrides."""
    p = dict(detector.default_params)
    rid = detector.rule_id
    overrides: dict[str, dict] = {
        "RULE-001": {
            "max_failures": settings.rule_bruteforce_max_failures,
            "window_seconds": settings.rule_bruteforce_window_seconds,
        },
        "RULE-002": {
            "unique_users": settings.rule_spray_unique_users,
            "window_seconds": settings.rule_spray_window_seconds,
        },
        "RULE-003": {
            "unique_ports": settings.rule_portscan_unique_ports,
            "window_seconds": settings.rule_portscan_window_seconds,
        },
        "RULE-006": {
            "bytes_threshold": settings.rule_exfil_bytes_threshold,
            "window_seconds": settings.rule_exfil_window_seconds,
        },
    }
    p.update(overrides.get(rid, {}))
    return p


class DetectionEngine:
    def __init__(self, redis_client: redis.Redis) -> None:
        self._windows = WindowStore(redis_client)
        self._detectors: list[Detector] = [cls() for cls in RULE_DETECTORS]  # type: ignore[abstract]
        self._params = {d.rule_id: _resolve_params(d) for d in self._detectors}
        self._disabled: set[str] = set()

    @property
    def detectors(self) -> list[Detector]:
        return self._detectors

    def catalogue(self) -> list[dict]:
        out = []
        for d in self._detectors:
            entry = d.catalogue_entry()
            entry["parameters"] = self._params[d.rule_id]
            entry["enabled"] = d.rule_id not in self._disabled
            entry["description"] = (d.__doc__ or "").strip().split("\n")[0]
            out.append(entry)
        return out

    def set_enabled(self, rule_id: str, enabled: bool) -> None:
        if enabled:
            self._disabled.discard(rule_id)
        else:
            self._disabled.add(rule_id)

    async def evaluate(self, event: SecurityEvent) -> list[Detection]:
        started = time.perf_counter()
        detections: list[Detection] = []
        for detector in self._detectors:
            if detector.rule_id in self._disabled:
                continue
            try:
                if not detector.applies_to(event):
                    continue
                ctx = DetectorContext(windows=self._windows, params=self._params[detector.rule_id])
                result = await detector.evaluate(event, ctx)
                if result is not None:
                    result.triggered_at = datetime.now(UTC)
                    detections.append(result)
            except Exception as exc:  # pragma: no cover - defensive isolation
                log.error(
                    "detector_error",
                    rule_id=detector.rule_id,
                    event_id=str(event.event_id),
                    error=str(exc),
                )
        DETECTION_LATENCY.observe(time.perf_counter() - started)
        return detections
