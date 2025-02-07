"""Kubernetes cluster health monitoring with mock fallback."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import (
    ClusterEvent,
    ClusterOverview,
    HealthStatus,
    NodeInfo,
)

logger = get_logger(__name__)
settings = get_settings()

_MOCK_NODES = [
    {"name": "node-control-plane", "roles": ["control-plane", "master"], "cpu": "4", "mem": "8Gi"},
    {"name": "node-worker-1", "roles": ["worker"], "cpu": "8", "mem": "16Gi"},
    {"name": "node-worker-2", "roles": ["worker"], "cpu": "8", "mem": "16Gi"},
]

_MOCK_EVENTS = [
    {"reason": "Pulled", "message": "Successfully pulled image 'nginx:latest'", "kind": "Pod", "type": "Normal", "count": 1},
    {"reason": "BackOff", "message": "Back-off restarting failed container", "kind": "Pod", "type": "Warning", "count": 5},
    {"reason": "Scheduled", "message": "Successfully assigned default/api-server-xyz to node-worker-1", "kind": "Pod", "type": "Normal", "count": 1},
    {"reason": "OOMKilling", "message": "Memory limit exceeded, killing container", "kind": "Pod", "type": "Warning", "count": 2},
    {"reason": "ScalingReplicaSet", "message": "Scaled up replica set frontend-abc to 3", "kind": "Deployment", "type": "Normal", "count": 1},
]


def _age_str(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    return f"{hours // 24}d"


def _mock_node(raw: dict[str, Any], idx: int) -> NodeInfo:
    cpu_pct = random.uniform(20, 85)
    mem_pct = random.uniform(30, 75)
    status = HealthStatus.HEALTHY if cpu_pct < 80 else HealthStatus.DEGRADED
    return NodeInfo(
        name=raw["name"],
        status=status,
        roles=raw["roles"],
        cpu_capacity=f"{raw['cpu']} cores",
        memory_capacity=raw["mem"],
        cpu_usage=f"{cpu_pct:.1f}%",
        memory_usage=f"{mem_pct:.1f}%",
        pod_count=random.randint(8, 24),
        age=_age_str(random.randint(1440, 43200)),
    )


def _mock_cluster_overview() -> ClusterOverview:
    nodes = [_mock_node(n, i) for i, n in enumerate(_MOCK_NODES)]
    degraded = any(n.status != HealthStatus.HEALTHY for n in nodes)
    return ClusterOverview(
        name="infra-os-cluster",
        version="v1.29.2",
        status=HealthStatus.DEGRADED if degraded else HealthStatus.HEALTHY,
        node_count=len(nodes),
        pod_count=random.randint(24, 48),
        deployment_count=random.randint(8, 16),
        namespace_count=6,
        nodes=nodes,
        mock_mode=True,
    )


def _mock_events() -> list[ClusterEvent]:
    events = []
    now = datetime.utcnow()
    for i, ev in enumerate(_MOCK_EVENTS):
        offset = timedelta(minutes=random.randint(1, 60))
        events.append(
            ClusterEvent(
                name=f"event-{i:04d}",
                namespace=random.choice(["default", "kube-system", "monitoring"]),
                reason=ev["reason"],
                message=ev["message"],
                kind=ev["kind"],
                count=ev["count"],
                event_type=ev["type"],
                first_time=(now - timedelta(hours=2)).isoformat(),
                last_time=(now - offset).isoformat(),
            )
        )
    return events


class ClusterMonitor:
    """Monitor Kubernetes cluster health, falling back to mock data."""

    def __init__(self) -> None:
        self._client: Any = None
        self._mock = settings.k8s_mock_mode
        if not self._mock:
            self._init_k8s_client()

    def _init_k8s_client(self) -> None:
        try:
            from kubernetes import client, config as k8s_config  # type: ignore[import]
            if settings.k8s_in_cluster:
                k8s_config.load_incluster_config()
            else:
                k8s_config.load_kube_config(config_file=settings.kubeconfig_path or None)
            self._client = client
            logger.info("Kubernetes client initialized (real cluster)")
        except Exception as exc:
            logger.warning("K8s client init failed, switching to mock: %s", exc)
            self._mock = True

    def get_cluster_overview(self) -> ClusterOverview:
        if self._mock:
            return _mock_cluster_overview()
        return self._real_cluster_overview()

    def _real_cluster_overview(self) -> ClusterOverview:
        v1 = self._client.CoreV1Api()
        nodes_resp = v1.list_node()
        nodes = []
        for n in nodes_resp.items:
            roles = [
                k.split("/")[-1]
                for k in (n.metadata.labels or {})
                if k.startswith("node-role.kubernetes.io/")
            ]
            status = HealthStatus.HEALTHY
            for cond in n.status.conditions or []:
                if cond.type == "Ready" and cond.status != "True":
                    status = HealthStatus.CRITICAL
            nodes.append(
                NodeInfo(
                    name=n.metadata.name,
                    status=status,
                    roles=roles or ["worker"],
                    cpu_capacity=n.status.capacity.get("cpu", "N/A"),
                    memory_capacity=n.status.capacity.get("memory", "N/A"),
                    pod_count=0,
                    age=_age_str(0),
                )
            )
        pods = v1.list_pod_for_all_namespaces()
        namespaces = v1.list_namespace()
        apps = self._client.AppsV1Api()
        deployments = apps.list_deployment_for_all_namespaces()
        return ClusterOverview(
            name="production-cluster",
            version="v1.29.x",
            status=HealthStatus.HEALTHY,
            node_count=len(nodes),
            pod_count=len(pods.items),
            deployment_count=len(deployments.items),
            namespace_count=len(namespaces.items),
            nodes=nodes,
            mock_mode=False,
        )

    def get_events(self) -> list[ClusterEvent]:
        if self._mock:
            return _mock_events()
        try:
            v1 = self._client.CoreV1Api()
            resp = v1.list_event_for_all_namespaces(limit=50)
            return [
                ClusterEvent(
                    name=e.metadata.name or "",
                    namespace=e.metadata.namespace or "default",
                    reason=e.reason or "",
                    message=e.message or "",
                    kind=e.involved_object.kind or "",
                    count=e.count or 1,
                    event_type=e.type or "Normal",
                    first_time=str(e.first_timestamp or ""),
                    last_time=str(e.last_timestamp or ""),
                )
                for e in resp.items
            ]
        except Exception as exc:
            logger.error("Failed to get events: %s", exc)
            return _mock_events()
