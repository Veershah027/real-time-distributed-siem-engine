"""Stream-processing pipeline: validate → normalize → detect → persist → alert.

Runs inside the ``app.worker`` process, one instance per consumer.  Postgres and
Redis writes are batched; the broker offset is committed only after a batch is
durably persisted (at-least-once, with event-id idempotency making it
effectively-once for storage).
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import UTC, datetime, timedelta

import orjson
import redis.asyncio as redis

from app.core.logging import get_logger
from app.core.metrics import (
    ALERTS_CORRELATED,
    ALERTS_CREATED,
    EVENTS_DUPLICATE,
    EVENTS_INGESTED,
    EVENTS_INVALID,
    EVENTS_PER_SECOND,
    EVENTS_PERSISTED,
    PIPELINE_LATENCY,
)
from app.detection.anomaly import StatisticalAnomalyDetector
from app.detection.correlation import AlertCorrelator
from app.detection.engine import DetectionEngine
from app.detection.ml import IsolationForestDetector
from app.schemas.alert import AlertRead
from app.schemas.enums import AlertStatus, DetectionKind, Severity
from app.schemas.event import EventRead, SecurityEvent
from app.storage.db import session_scope
from app.storage.redis_client import CHANNEL_ALERTS, CHANNEL_EVENTS, CHANNEL_METRICS
from app.storage.repositories import AlertRepository, EventRepository

log = get_logger("streaming.pipeline")

_DEDUP_KEY = "siem:seen-events"
_DEDUP_TTL = 600
_METRIC_HASH = "siem:metrics:rolling"


class Pipeline:
    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client
        self.engine = DetectionEngine(redis_client)
        self.anomaly = StatisticalAnomalyDetector(redis_client)
        self.ml = IsolationForestDetector()
        self._minute_bucket = self._current_minute()
        self._minute_counter: Counter[str] = Counter()
        self._minute_ips: set[str] = set()
        self._window_events = 0
        self._window_started = time.monotonic()

    @staticmethod
    def _current_minute() -> datetime:
        now = datetime.now(UTC)
        return now.replace(second=0, microsecond=0)

    # ------------------------------------------------------------------ #
    async def process_batch(self, raw_events: list[dict]) -> None:
        started = time.perf_counter()
        valid: list[SecurityEvent] = []

        # --- validate + normalize + dedupe ---
        for raw in raw_events:
            EVENTS_INGESTED.inc()
            try:
                event = SecurityEvent.from_raw(raw)
            except Exception as exc:
                EVENTS_INVALID.labels(reason="validation").inc()
                log.warning("event_rejected", error=str(exc))
                continue
            valid.append(event)

        if not valid:
            return

        ids = [str(e.event_id) for e in valid]
        pipe = self.redis.pipeline()
        for eid in ids:
            pipe.sismember(_DEDUP_KEY, eid)
        seen_flags = await pipe.execute()
        fresh = [e for e, seen in zip(valid, seen_flags, strict=True) if not seen]
        dupes = len(valid) - len(fresh)
        if dupes:
            EVENTS_DUPLICATE.inc(dupes)
        if not fresh:
            return

        pipe = self.redis.pipeline()
        pipe.sadd(_DEDUP_KEY, *[str(e.event_id) for e in fresh])
        pipe.expire(_DEDUP_KEY, _DEDUP_TTL)
        await pipe.execute()

        # --- detect ---
        all_detections = []
        for event in fresh:
            detections = await self.engine.evaluate(event)
            for d in detections:
                all_detections.append((event, d))

        # --- persist events + alerts in one transaction ---
        alert_payloads: list[AlertRead] = []
        async with session_scope() as session:
            event_repo = EventRepository(session)
            alert_repo = AlertRepository(session)
            correlator = AlertCorrelator(alert_repo)

            written = await event_repo.bulk_insert(fresh)
            EVENTS_PERSISTED.inc(written)

            for _event, detection in all_detections:
                alert, created = await correlator.apply(detection)
                await session.flush()
                if created:
                    ALERTS_CREATED.labels(rule_id=alert.rule_id, severity=alert.severity).inc()
                else:
                    ALERTS_CORRELATED.labels(rule_id=alert.rule_id).inc()
                alert_payloads.append(AlertRead.model_validate(alert))

        # --- publish to real-time subscribers ---
        await self._publish_events(fresh)
        for payload in alert_payloads:
            await self.redis.publish(CHANNEL_ALERTS, payload.model_dump_json())

        # --- rolling metrics + anomaly feed ---
        await self._update_metrics(fresh, all_detections)

        PIPELINE_LATENCY.observe((time.perf_counter() - started) / max(len(fresh), 1))

    # ------------------------------------------------------------------ #
    async def _publish_events(self, events: list[SecurityEvent]) -> None:
        # Cap fan-out chatter: publish at most 100 events per batch to the WS channel.
        pipe = self.redis.pipeline()
        for event in events[:100]:
            pipe.publish(
                CHANNEL_EVENTS,
                orjson.dumps(EventRead.model_validate(event.model_dump()).model_dump(mode="json")),
            )
        await pipe.execute()

    async def _update_metrics(self, events: list[SecurityEvent], detections: list) -> None:
        now_minute = self._current_minute()
        self._window_events += len(events)

        for e in events:
            self._minute_counter["events"] += 1
            if e.event_type.value == "authentication_failure":
                self._minute_counter["auth_failures"] += 1
            if e.event_type.value == "db_error":
                self._minute_counter["db_errors"] += 1
            if e.event_type.value == "firewall_deny":
                self._minute_counter["firewall_denies"] += 1
            self._minute_counter["bytes_out"] += e.bytes_out
            if e.source_ip:
                self._minute_ips.add(e.source_ip)

        # events/sec over a ~5s sliding measurement
        elapsed = time.monotonic() - self._window_started
        if elapsed >= 5:
            eps = self._window_events / elapsed
            EVENTS_PER_SECOND.set(eps)
            await self.redis.hset(_METRIC_HASH, mapping={"events_per_second": f"{eps:.2f}"})
            await self.redis.expire(_METRIC_HASH, 300)
            await self.redis.publish(
                CHANNEL_METRICS, orjson.dumps({"events_per_second": round(eps, 2)})
            )
            self._window_events = 0
            self._window_started = time.monotonic()

        # per-minute rollover → feed anomaly + ML
        if now_minute != self._minute_bucket:
            await self._flush_minute(self._minute_bucket)
            self._minute_bucket = now_minute
            self._minute_counter = Counter()
            self._minute_ips = set()

    async def _flush_minute(self, minute: datetime) -> None:
        c = self._minute_counter
        features = {
            "events_per_min": float(c["events"]),
            "auth_failures_per_min": float(c["auth_failures"]),
            "unique_source_ips": float(len(self._minute_ips)),
            "outbound_mib_per_min": round(c["bytes_out"] / (1024 * 1024), 3),
            "db_errors_per_min": float(c["db_errors"]),
            "firewall_denies_per_min": float(c["firewall_denies"]),
        }
        await self.redis.hset(
            "siem:metrics:last_minute",
            mapping={k: str(v) for k, v in features.items()} | {"minute": minute.isoformat()},
        )
        await self.redis.expire("siem:metrics:last_minute", 300)

        anomalies = []
        for metric, value in features.items():
            res = await self.anomaly.observe(metric, value)
            if res is not None:
                anomalies.append(res)

        ml_res = self.ml.observe(features)

        for res in anomalies:
            await self._raise_anomaly_alert(res, minute)
        if ml_res is not None and ml_res.is_anomaly:
            await self._raise_ml_alert(ml_res, minute, features)

    async def _raise_anomaly_alert(self, res, minute: datetime) -> None:
        from app.detection.base import Detection

        det = Detection(
            rule_id="ANOM-001",
            kind=DetectionKind.ANOMALY,
            title=f"Statistical anomaly: {res.metric}",
            description=res.anomaly_reason,
            severity=Severity.MEDIUM if res.anomaly_score < 0.85 else Severity.HIGH,
            confidence=round(min(0.95, res.anomaly_score), 2),
            correlation_key=f"anomaly:{res.metric}:{minute.isoformat()}",
            source_ip=None,
            affected_host=None,
            recommended_action=(
                "Review what changed in the environment during this minute. "
                "Correlate with rule-based alerts and simulator activity."
            ),
            anomaly_score=res.anomaly_score,
            metadata={
                "metric": res.metric,
                "value": res.value,
                "baseline_mean": res.baseline_mean,
                "baseline_std": res.baseline_std,
                "z_score": res.z_score,
            },
            triggered_at=datetime.now(UTC),
        )
        await self._persist_standalone_alert(det)

    async def _raise_ml_alert(self, ml_res, minute: datetime, features: dict) -> None:
        from app.detection.base import Detection

        det = Detection(
            rule_id="ML-001",
            kind=DetectionKind.ML,
            title="Isolation Forest flagged an anomalous minute",
            description=ml_res.reason,
            severity=Severity.MEDIUM,
            confidence=round(min(0.9, ml_res.score), 2),
            correlation_key=f"ml:{minute.isoformat()}",
            source_ip=None,
            affected_host=None,
            recommended_action=(
                "Demo/research model. Treat as a hint to inspect this minute's "
                "traffic mix; confirm with deterministic rules before acting."
            ),
            anomaly_score=ml_res.score,
            metadata={"features": features, "model": "IsolationForest"},
            triggered_at=datetime.now(UTC),
        )
        await self._persist_standalone_alert(det)

    async def _persist_standalone_alert(self, detection) -> None:
        async with session_scope() as session:
            correlator = AlertCorrelator(AlertRepository(session))
            alert, created = await correlator.apply(detection)
            await session.flush()
            if created:
                ALERTS_CREATED.labels(rule_id=alert.rule_id, severity=alert.severity).inc()
            payload = AlertRead.model_validate(alert)
        await self.redis.publish(CHANNEL_ALERTS, payload.model_dump_json())

    async def refresh_active_alert_gauge(self) -> None:
        async with session_scope() as session:
            counts = await AlertRepository(session).counts_by_status_severity()
        active: Counter[str] = Counter()
        for key, n in counts.items():
            status, sev = key.split(":")
            if status in {AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED}:
                active[sev] += n
        for sev in ("info", "low", "medium", "high", "critical"):
            from app.core.metrics import ACTIVE_ALERTS

            ACTIVE_ALERTS.labels(severity=sev).set(active.get(sev, 0))
        await self.redis.hset(
            "siem:metrics:active_alerts",
            mapping={k: str(v) for k, v in active.items()} or {"none": "0"},
        )
        await self.redis.expire("siem:metrics:active_alerts", 120)

    async def housekeeping_since(self) -> datetime:
        return datetime.now(UTC) - timedelta(minutes=5)
