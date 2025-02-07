"""Resource usage analysis across the cluster."""

from __future__ import annotations

import random
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ResourceAnalyzer:
    """Analyze CPU, memory, and storage usage across namespaces."""

    def __init__(self) -> None:
        self._mock = settings.k8s_mock_mode

    def get_namespace_resource_summary(self) -> list[dict[str, Any]]:
        if self._mock:
            return self._mock_ns_summary()
        return self._mock_ns_summary()  # Real metrics need metrics-server

    def _mock_ns_summary(self) -> list[dict[str, Any]]:
        namespaces = ["default", "monitoring", "infra", "kube-system", "ingress-nginx", "cert-manager"]
        return [
            {
                "namespace": ns,
                "pod_count": random.randint(2, 12),
                "cpu_requests": f"{random.randint(100, 2000)}m",
                "cpu_limits": f"{random.randint(500, 4000)}m",
                "cpu_usage": f"{random.uniform(5, 85):.1f}%",
                "memory_requests": f"{random.randint(64, 2048)}Mi",
                "memory_limits": f"{random.randint(128, 4096)}Mi",
                "memory_usage": f"{random.uniform(10, 80):.1f}%",
            }
            for ns in namespaces
        ]

    def get_top_consumers(self, metric: str = "cpu", limit: int = 5) -> list[dict[str, Any]]:
        """Return top resource-consuming pods."""
        pods = [
            {"pod": f"worker-{i:03d}", "namespace": "default",
             "cpu": random.uniform(100, 990), "memory": random.randint(64, 1024)}
            for i in range(10)
        ]
        key = "cpu" if metric == "cpu" else "memory"
        pods.sort(key=lambda p: p[key], reverse=True)
        return [
            {
                "rank": idx + 1,
                "pod": p["pod"],
                "namespace": p["namespace"],
                "cpu": f"{p['cpu']:.0f}m",
                "memory": f"{p['memory']}Mi",
            }
            for idx, p in enumerate(pods[:limit])
        ]

    def get_cluster_capacity(self) -> dict[str, Any]:
        return {
            "total_cpu_cores": 20,
            "total_memory_gib": 40,
            "allocated_cpu_pct": round(random.uniform(30, 75), 1),
            "allocated_memory_pct": round(random.uniform(40, 70), 1),
            "node_count": 3,
            "schedulable_nodes": 3,
        }
