"""ML-based anomaly detection on infrastructure metrics."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import Alert, AlertSeverity

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class AnomalyResult:
    metric_name: str
    current_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    is_anomaly: bool
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)


def _z_score_detect(values: list[float], threshold: float = 2.5) -> list[AnomalyResult]:
    if len(values) < 5:
        return []
    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr[:-1]))
    std = float(np.std(arr[:-1])) or 1.0
    current = values[-1]
    z = abs(current - mean) / std
    severity = (
        AlertSeverity.CRITICAL if z > 4.0
        else AlertSeverity.WARNING if z > threshold
        else AlertSeverity.INFO
    )
    return [
        AnomalyResult(
            metric_name="metric",
            current_value=current,
            baseline_mean=mean,
            baseline_std=std,
            z_score=z,
            is_anomaly=z > threshold,
            severity=severity,
        )
    ]


class AnomalyDetector:
    """Detect anomalies in metrics using statistical and ML methods."""

    def __init__(self) -> None:
        self._history: dict[str, list[float]] = {}
        self._window = 20  # number of samples to keep

    def record_metric(self, name: str, value: float) -> AnomalyResult | None:
        if name not in self._history:
            self._history[name] = []
        self._history[name].append(value)
        if len(self._history[name]) > self._window:
            self._history[name] = self._history[name][-self._window:]
        results = _z_score_detect(self._history[name])
        if results:
            results[0].metric_name = name
            if results[0].is_anomaly:
                logger.warning(
                    "Anomaly detected: %s z=%.2f val=%.2f",
                    name, results[0].z_score, value
                )
            return results[0]
        return None

    def detect_from_prometheus(self, metrics: list[dict[str, Any]]) -> list[Alert]:
        alerts: list[Alert] = []
        for m in metrics:
            name = m.get("metric_name", "unknown")
            value = m.get("value", 0.0)
            result = self.record_metric(name, float(value))
            if result and result.is_anomaly:
                alerts.append(
                    Alert(
                        id=f"anomaly-{name}-{int(result.timestamp.timestamp())}",
                        name=f"Anomaly: {name}",
                        severity=result.severity,
                        message=(
                            f"{name} is {result.current_value:.2f} "
                            f"(baseline: {result.baseline_mean:.2f} ± {result.baseline_std:.2f}, "
                            f"z-score: {result.z_score:.2f})"
                        ),
                        timestamp=result.timestamp,
                    )
                )
        return alerts

    def mock_anomaly_scan(self) -> list[AnomalyResult]:
        """Generate realistic mock anomaly scan results."""
        metrics = {
            "cpu_usage_pct": random.uniform(10, 95),
            "memory_usage_pct": random.uniform(20, 90),
            "pod_restart_count": random.randint(0, 50),
            "request_latency_ms": random.uniform(10, 5000),
            "error_rate_pct": random.uniform(0, 25),
        }
        results = []
        for name, value in metrics.items():
            result = self.record_metric(name, value)
            if result:
                results.append(result)
        return results
