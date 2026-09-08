"""Optional unsupervised ML layer — Isolation Forest.

Disabled unless ``SIEM_ENABLE_ML=true`` *and* the ``ml`` extra is installed
(`pip install -e ".[ml]"`).  This is a research/demo detector: it is trained on
a rolling buffer of recent per-minute feature vectors and flags outliers. It is
**not** a production threat-detection model and never overrides a rule verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("detection.ml")

_FEATURES = (
    "events_per_min",
    "auth_failures_per_min",
    "unique_source_ips",
    "outbound_mib_per_min",
    "db_errors_per_min",
    "firewall_denies_per_min",
)


@dataclass(slots=True)
class MLResult:
    is_anomaly: bool
    score: float
    features: dict[str, float]
    reason: str


class IsolationForestDetector:
    """Lazily-loaded wrapper. No-ops cleanly when ML is disabled/unavailable."""

    def __init__(self, *, contamination: float = 0.05, buffer_size: int = 720) -> None:
        self.enabled = settings.enable_ml
        self.contamination = contamination
        self.buffer_size = buffer_size
        self._buffer: list[list[float]] = []
        self._model: Any = None
        self._trained = False
        if self.enabled:
            try:
                import sklearn  # noqa: F401
            except ImportError:
                log.warning("ml_disabled_missing_dependency", hint="pip install -e '.[ml]'")
                self.enabled = False

    def _vectorize(self, feats: dict[str, float]) -> list[float]:
        return [float(feats.get(name, 0.0)) for name in _FEATURES]

    def observe(self, feats: dict[str, float]) -> MLResult | None:
        if not self.enabled:
            return None
        vec = self._vectorize(feats)
        self._buffer.append(vec)
        if len(self._buffer) > self.buffer_size:
            self._buffer.pop(0)

        if len(self._buffer) < max(60, self.buffer_size // 6):
            return None

        try:
            from sklearn.ensemble import IsolationForest

            # Retrain periodically on the rolling buffer (cheap at this scale).
            if self._model is None or len(self._buffer) % 30 == 0:
                model = IsolationForest(
                    contamination=self.contamination,
                    n_estimators=100,
                    random_state=42,
                )
                model.fit(self._buffer[:-1])
                self._model = model
                self._trained = True

            model = self._model
            raw = float(model.decision_function([vec])[0])
            pred = int(model.predict([vec])[0])
            score = max(0.0, min(1.0, 0.5 - raw))
            if pred == -1:
                top = sorted(feats.items(), key=lambda kv: -kv[1])[:3]
                return MLResult(
                    is_anomaly=True,
                    score=round(score, 3),
                    features=feats,
                    reason=(
                        "Isolation Forest flagged this minute as an outlier; "
                        "largest contributors: " + ", ".join(f"{k}={v:.1f}" for k, v in top)
                    ),
                )
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("ml_inference_failed", error=str(exc))
        return None
