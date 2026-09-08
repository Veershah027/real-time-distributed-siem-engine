"""Statistical anomaly detection.

A deterministic, explainable baseline — **not** a production IDS/UEBA model.
For each named metric we maintain an exponentially-weighted mean and variance
in Redis (Welford-style EWMA).  A new observation is anomalous when its
z-score exceeds a configurable threshold *and* we have seen enough samples to
trust the baseline.

The engine feeds this per-minute aggregates: events/sec, auth failures/min,
outbound MiB/min, db errors/min, etc.  The design intentionally keeps the
interface (``observe``) narrow so an ML model could be dropped in behind it.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

import redis.asyncio as redis

from app.core.config import settings


@dataclass(slots=True)
class AnomalyResult:
    metric: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    anomaly_score: float  # 0..1 squashed
    anomaly_reason: str
    samples: int


class StatisticalAnomalyDetector:
    def __init__(
        self,
        client: redis.Redis,
        *,
        alpha: float | None = None,
        z_threshold: float | None = None,
        min_samples: int | None = None,
    ) -> None:
        self._r = client
        self.alpha = alpha if alpha is not None else settings.anomaly_ewma_alpha
        self.z_threshold = (
            z_threshold if z_threshold is not None else settings.anomaly_zscore_threshold
        )
        self.min_samples = (
            min_samples if min_samples is not None else settings.anomaly_min_samples
        )

    def _key(self, metric: str) -> str:
        return f"siem:anomaly:{metric}"

    async def observe(self, metric: str, value: float) -> AnomalyResult | None:
        key = self._key(metric)
        raw = await self._r.get(key)
        state = json.loads(raw) if raw else {"mean": value, "var": 0.0, "n": 0}

        mean, var, n = state["mean"], state["var"], int(state["n"])
        std = math.sqrt(var)

        z = 0.0 if std < 1e-9 else (value - mean) / std
        result: AnomalyResult | None = None
        if n >= self.min_samples and abs(z) >= self.z_threshold:
            score = 1.0 - math.exp(-((abs(z) - self.z_threshold) ** 2) / 8.0)
            direction = "above" if z > 0 else "below"
            result = AnomalyResult(
                metric=metric,
                value=round(value, 3),
                baseline_mean=round(mean, 3),
                baseline_std=round(std, 3),
                z_score=round(z, 2),
                anomaly_score=round(min(1.0, 0.5 + 0.5 * score), 3),
                anomaly_reason=(
                    f"{metric} = {value:.1f} is {abs(z):.1f}σ {direction} the "
                    f"rolling baseline of {mean:.1f} ± {std:.1f} (n={n})"
                ),
                samples=n,
            )

        # EWMA update (do not let a huge spike poison the baseline too fast:
        # dampen alpha when the point is extreme)
        eff_alpha = self.alpha / (1 + max(0.0, abs(z) - self.z_threshold))
        delta = value - mean
        new_mean = mean + eff_alpha * delta
        new_var = (1 - eff_alpha) * (var + eff_alpha * delta * delta)
        await self._r.set(
            key,
            json.dumps({"mean": new_mean, "var": new_var, "n": n + 1}),
            ex=7 * 24 * 3600,
        )
        return result

    async def baseline(self, metric: str) -> dict[str, float]:
        raw = await self._r.get(self._key(metric))
        if not raw:
            return {"mean": 0.0, "std": 0.0, "n": 0}
        s = json.loads(raw)
        return {"mean": s["mean"], "std": math.sqrt(s["var"]), "n": s["n"]}
