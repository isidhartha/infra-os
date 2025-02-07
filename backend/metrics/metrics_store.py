"""In-memory metrics store for real-time streaming."""

from __future__ import annotations

import random
import time
from collections import deque
from typing import Any

_MAX_SAMPLES = 60  # keep last 60 data points per metric


class MetricsStore:
    """Thread-safe, in-memory circular buffer for metrics time series."""

    def __init__(self) -> None:
        self._series: dict[str, deque[dict[str, Any]]] = {}

    def record(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        if name not in self._series:
            self._series[name] = deque(maxlen=_MAX_SAMPLES)
        self._series[name].append({
            "timestamp": time.time(),
            "value": value,
            "labels": labels or {},
        })

    def get_series(self, name: str, last_n: int = 20) -> list[dict[str, Any]]:
        series = self._series.get(name, deque())
        return list(series)[-last_n:]

    def get_latest(self, name: str) -> float | None:
        series = self._series.get(name)
        if series:
            return series[-1]["value"]
        return None

    def generate_mock_snapshot(self) -> dict[str, Any]:
        """Generate a realistic mock metrics snapshot for streaming."""
        now = time.time()
        return {
            "timestamp": now,
            "cluster": {
                "cpu_usage_pct": round(random.uniform(25, 80), 1),
                "memory_usage_pct": round(random.uniform(40, 75), 1),
                "pod_count": random.randint(22, 30),
                "node_count": 3,
                "alert_count": random.randint(2, 6),
            },
            "nodes": [
                {
                    "name": f"node-worker-{i}",
                    "cpu_pct": round(random.uniform(15, 90), 1),
                    "memory_pct": round(random.uniform(30, 85), 1),
                    "pod_count": random.randint(8, 20),
                }
                for i in range(1, 3)
            ],
            "top_pods": [
                {
                    "name": f"worker-{i:03d}",
                    "namespace": "default",
                    "cpu_millicores": random.randint(50, 950),
                    "memory_mib": random.randint(64, 512),
                    "restarts": random.randint(0, 10),
                }
                for i in range(5)
            ],
            "request_rate": round(random.uniform(100, 5000), 1),
            "error_rate_pct": round(random.uniform(0, 5), 2),
            "p99_latency_ms": round(random.uniform(10, 500), 1),
        }

    def get_all_series_names(self) -> list[str]:
        return list(self._series.keys())
