"""Statistical anomaly detector."""

from __future__ import annotations

from app.detection.anomaly import StatisticalAnomalyDetector


async def test_no_anomaly_before_min_samples(redis_client):
    det = StatisticalAnomalyDetector(redis_client, min_samples=20, z_threshold=3.0)
    for _ in range(10):
        assert await det.observe("events_per_min", 100.0) is None


async def test_detects_spike_after_baseline(redis_client):
    det = StatisticalAnomalyDetector(redis_client, alpha=0.3, z_threshold=3.0, min_samples=15)
    for _ in range(40):
        await det.observe("events_per_min", 100.0 + (hash(str(_)) % 7))
    result = await det.observe("events_per_min", 5000.0)
    assert result is not None
    assert result.z_score > 3.0
    assert 0.5 <= result.anomaly_score <= 1.0
    assert "above" in result.anomaly_reason


async def test_stable_series_no_false_positive(redis_client):
    det = StatisticalAnomalyDetector(redis_client, z_threshold=3.5, min_samples=15)
    hits = 0
    for i in range(60):
        r = await det.observe("auth_failures_per_min", 10.0 + (i % 3))
        hits += r is not None
    assert hits == 0


async def test_baseline_readback(redis_client):
    det = StatisticalAnomalyDetector(redis_client)
    for _ in range(5):
        await det.observe("m", 50.0)
    base = await det.baseline("m")
    assert base["n"] == 5
    assert 40 <= base["mean"] <= 60
