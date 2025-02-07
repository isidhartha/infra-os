"""Pod lifecycle operations (list, restart, delete)."""

from __future__ import annotations

import random
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import PodInfo, PodPhase, RemediationResult

logger = get_logger(__name__)
settings = get_settings()

_MOCK_POD_TEMPLATES = [
    {"prefix": "api-gateway", "ns": "default", "restarts": 0},
    {"prefix": "auth-service", "ns": "default", "restarts": 2},
    {"prefix": "frontend", "ns": "default", "restarts": 0},
    {"prefix": "worker", "ns": "default", "restarts": 8},
    {"prefix": "crash-loop-demo", "ns": "default", "restarts": 47},
    {"prefix": "prometheus-operator", "ns": "monitoring", "restarts": 0},
    {"prefix": "grafana", "ns": "monitoring", "restarts": 1},
    {"prefix": "redis", "ns": "infra", "restarts": 0},
    {"prefix": "postgres", "ns": "infra", "restarts": 0},
    {"prefix": "kube-dns", "ns": "kube-system", "restarts": 0},
    {"prefix": "kube-proxy", "ns": "kube-system", "restarts": 0},
]

_NODES = ["node-worker-1", "node-worker-2", "node-control-plane"]


def _suffix() -> str:
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=5))


def _mock_pod(tmpl: dict[str, Any]) -> PodInfo:
    restarts = tmpl["restarts"]
    if restarts > 20:
        phase = random.choice([PodPhase.RUNNING, PodPhase.FAILED])
        ready = phase == PodPhase.RUNNING
    elif restarts > 5:
        phase = PodPhase.RUNNING
        ready = random.choice([True, False])
    else:
        phase = PodPhase.RUNNING
        ready = True

    age_min = random.randint(30, 4320)
    age = f"{age_min}m" if age_min < 60 else f"{age_min // 60}h"
    cpu = f"{random.uniform(1, 950):.0f}m"
    mem = f"{random.randint(32, 512)}Mi"

    return PodInfo(
        name=f"{tmpl['prefix']}-{_suffix()}",
        namespace=tmpl["ns"],
        phase=phase,
        ready=ready,
        restarts=restarts + random.randint(0, 2),
        node=random.choice(_NODES),
        age=age,
        cpu_usage=cpu,
        memory_usage=mem,
        labels={"app": tmpl["prefix"]},
    )


class PodManager:
    """Manage Kubernetes pods with mock fallback."""

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
            logger.warning("K8s client unavailable for pods: %s", exc)
            self._mock = True

    def list_pods(self, namespace: str = "") -> list[PodInfo]:
        if self._mock:
            pods = [_mock_pod(t) for t in _MOCK_POD_TEMPLATES]
            if namespace:
                pods = [p for p in pods if p.namespace == namespace]
            return pods
        return self._real_pods(namespace)

    def _real_pods(self, namespace: str) -> list[PodInfo]:
        v1 = self._client.CoreV1Api()
        try:
            resp = (
                v1.list_namespaced_pod(namespace)
                if namespace
                else v1.list_pod_for_all_namespaces()
            )
            result = []
            for p in resp.items:
                containers = p.status.container_statuses or []
                restarts = sum(c.restart_count or 0 for c in containers)
                ready = all(c.ready for c in containers) if containers else False
                phase = PodPhase(p.status.phase or "Unknown")
                result.append(
                    PodInfo(
                        name=p.metadata.name,
                        namespace=p.metadata.namespace,
                        phase=phase,
                        ready=ready,
                        restarts=restarts,
                        node=p.spec.node_name or "",
                        age="N/A",
                        labels=dict(p.metadata.labels or {}),
                    )
                )
            return result
        except Exception as exc:
            logger.error("Failed to list real pods: %s", exc)
            return [_mock_pod(t) for t in _MOCK_POD_TEMPLATES]

    def restart_pod(self, name: str, namespace: str) -> RemediationResult:
        if self._mock:
            logger.info("Mock restart pod %s/%s", namespace, name)
            return RemediationResult(
                success=True,
                action="restart",
                resource=f"{namespace}/{name}",
                message=f"Pod {name} deleted and will be recreated by its controller.",
            )
        try:
            v1 = self._client.CoreV1Api()
            v1.delete_namespaced_pod(name, namespace)
            return RemediationResult(
                success=True,
                action="restart",
                resource=f"{namespace}/{name}",
                message=f"Pod {name} deleted successfully.",
            )
        except Exception as exc:
            return RemediationResult(
                success=False,
                action="restart",
                resource=f"{namespace}/{name}",
                message=str(exc),
            )
