"""Prometheus metrics registry for the SIEM engine.

Exposed at ``GET /metrics`` (text format).  These counters are also mirrored
into Redis by the pipeline so the dashboard can render live rates without
scraping Prometheus.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

REGISTRY = CollectorRegistry()

EVENTS_INGESTED = Counter(
    "siem_events_ingested_total",
    "Raw events consumed from the broker",
    registry=REGISTRY,
)
EVENTS_INVALID = Counter(
    "siem_events_invalid_total",
    "Events rejected during validation/normalization",
    ["reason"],
    registry=REGISTRY,
)
EVENTS_PERSISTED = Counter(
    "siem_events_persisted_total",
    "Events written to PostgreSQL",
    registry=REGISTRY,
)
EVENTS_DUPLICATE = Counter(
    "siem_events_duplicate_total",
    "Events dropped as duplicates (idempotency)",
    registry=REGISTRY,
)
ALERTS_CREATED = Counter(
    "siem_alerts_created_total",
    "New alerts created",
    ["rule_id", "severity"],
    registry=REGISTRY,
)
ALERTS_CORRELATED = Counter(
    "siem_alerts_correlated_total",
    "Events folded into an existing alert instead of creating a new one",
    ["rule_id"],
    registry=REGISTRY,
)
DETECTION_LATENCY = Histogram(
    "siem_detection_latency_seconds",
    "Time to run the full detection engine on one event",
    registry=REGISTRY,
    buckets=(0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
PIPELINE_LATENCY = Histogram(
    "siem_pipeline_latency_seconds",
    "End-to-end per-event pipeline latency (consume -> persisted)",
    registry=REGISTRY,
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
CONSUMER_ERRORS = Counter(
    "siem_consumer_errors_total",
    "Broker consumer errors",
    ["kind"],
    registry=REGISTRY,
)
EVENTS_PER_SECOND = Gauge(
    "siem_events_per_second",
    "Rolling events/sec as measured by the pipeline",
    registry=REGISTRY,
)
ACTIVE_ALERTS = Gauge(
    "siem_active_alerts",
    "Alerts not in a terminal state",
    ["severity"],
    registry=REGISTRY,
)
