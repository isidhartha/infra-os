"""Deployment analytics and rollout tracking."""

from __future__ import annotations

import random
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import DeploymentInfo, HealthStatus

logger = get_logger(__name__)
settings = get_settings()

_MOCK_DEPLOYMENTS = [
    {"name": "api-gateway", "ns": "default", "image": "nginx:1.25", "strategy": "RollingUpdate"},
    {"name": "auth-service", "ns": "default", "image": "auth-service:v2.3.1", "strategy": "RollingUpdate"},
    {"name": "frontend", "ns": "default", "image": "frontend:latest", "strategy": "Recreate"},
    {"name": "worker", "ns": "default", "image": "worker:v1.8.0", "strategy": "RollingUpdate"},
    {"name": "prometheus-operator", "ns": "monitoring", "image": "prometheus-operator:v0.74", "strategy": "RollingUpdate"},
    {"name": "grafana", "ns": "monitoring", "image": "grafana/grafana:10.4", "strategy": "RollingUpdate"},
    {"name": "redis-cluster", "ns": "infra", "image": "redis:7.2-alpine", "strategy": "RollingUpdate"},
    {"name": "postgres", "ns": "infra", "image": "postgres:16", "strategy": "Recreate"},
]


def _mock_deployment(raw: dict[str, Any]) -> DeploymentInfo:
    desired = random.randint(1, 5)
    ready = random.randint(max(0, desired - 1), desired)
    available = ready
    updated = random.randint(ready, desired)
    status = (
        HealthStatus.HEALTHY if ready == desired
        else HealthStatus.DEGRADED if ready > 0
        else HealthStatus.CRITICAL
    )
    age_hours = random.randint(1, 720)
    age = f"{age_hours // 24}d" if age_hours >= 24 else f"{age_hours}h"
    return DeploymentInfo(
        name=raw["name"],
        namespace=raw["ns"],
        desired=desired,
        ready=ready,
        available=available,
        updated=updated,
        strategy=raw["strategy"],
        age=age,
        image=raw["image"],
        status=status,
    )


class DeploymentTracker:
    """Track Kubernetes deployments and rollout history."""

    def __init__(self) -> None:
        self._mock = settings.k8s_mock_mode
        self._client: Any = None
        if not self._mock:
            self._init_client()

    def _init_client(self) -> None:
        try:
            from kubernetes import client, config as k8s_config  # type: ignore[import]
            if settings.k8s_in_cluster:
                k8s_config.load_incluster_config()
            else:
                k8s_config.load_kube_config(config_file=settings.kubeconfig_path or None)
            self._client = client
        except Exception as exc:
            logger.warning("K8s client unavailable for deployments: %s", exc)
            self._mock = True

    def list_deployments(self, namespace: str = "") -> list[DeploymentInfo]:
        if self._mock:
            deployments = [_mock_deployment(d) for d in _MOCK_DEPLOYMENTS]
            if namespace:
                deployments = [d for d in deployments if d.namespace == namespace]
            return deployments
        return self._real_deployments(namespace)

    def _real_deployments(self, namespace: str) -> list[DeploymentInfo]:
        apps = self._client.AppsV1Api()
        try:
            if namespace:
                resp = apps.list_namespaced_deployment(namespace)
            else:
                resp = apps.list_deployment_for_all_namespaces()
            result = []
            for d in resp.items:
                spec = d.spec
                status = d.status
                ready = status.ready_replicas or 0
                desired = spec.replicas or 0
                health = (
                    HealthStatus.HEALTHY if ready == desired
                    else HealthStatus.DEGRADED if ready > 0
                    else HealthStatus.CRITICAL
                )
                containers = spec.template.spec.containers or []
                image = containers[0].image if containers else ""
                result.append(
                    DeploymentInfo(
                        name=d.metadata.name,
                        namespace=d.metadata.namespace,
                        desired=desired,
                        ready=ready,
                        available=status.available_replicas or 0,
                        updated=status.updated_replicas or 0,
                        strategy=spec.strategy.type if spec.strategy else "RollingUpdate",
                        age="N/A",
                        image=image,
                        status=health,
                    )
                )
            return result
        except Exception as exc:
            logger.error("Failed to list real deployments: %s", exc)
            return [_mock_deployment(d) for d in _MOCK_DEPLOYMENTS]

    def get_rollout_history(self, name: str, namespace: str = "default") -> list[dict[str, Any]]:
        """Return mock rollout history for a deployment."""
        return [
            {"revision": 3, "change_cause": "Upgrade to v2.3.1", "timestamp": "2026-05-17T14:00:00Z", "status": "complete"},
            {"revision": 2, "change_cause": "Scale to 3 replicas", "timestamp": "2026-05-15T09:30:00Z", "status": "complete"},
            {"revision": 1, "change_cause": "Initial deployment", "timestamp": "2026-05-10T08:00:00Z", "status": "complete"},
        ]
