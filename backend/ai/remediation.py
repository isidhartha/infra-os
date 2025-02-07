"""Automated remediation workflows for Kubernetes issues."""

from __future__ import annotations

from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import RemediationRequest, RemediationResult

logger = get_logger(__name__)
settings = get_settings()

_REMEDIATION_PLAYBOOKS: dict[str, dict[str, Any]] = {
    "restart_pod": {
        "description": "Delete pod to force controller recreation",
        "risk": "low",
        "auto_approved": True,
    },
    "scale_deployment": {
        "description": "Adjust deployment replica count",
        "risk": "medium",
        "auto_approved": True,
    },
    "rollback_deployment": {
        "description": "Roll back deployment to previous revision",
        "risk": "medium",
        "auto_approved": False,
    },
    "cordon_node": {
        "description": "Prevent new pods from scheduling on node",
        "risk": "high",
        "auto_approved": False,
    },
    "drain_node": {
        "description": "Evict all pods from node for maintenance",
        "risk": "high",
        "auto_approved": False,
    },
    "increase_memory_limit": {
        "description": "Patch deployment to increase memory limit",
        "risk": "low",
        "auto_approved": True,
    },
}


def suggest_remediation(issue_type: str, resource: str, namespace: str) -> list[dict[str, Any]]:
    """Suggest remediation actions for a given issue type."""
    suggestions: dict[str, list[str]] = {
        "CrashLoopBackOff": ["restart_pod", "rollback_deployment"],
        "OOMKilled": ["increase_memory_limit", "restart_pod"],
        "ImagePullBackOff": [],
        "Pending": ["scale_deployment"],
        "NodeNotReady": ["cordon_node", "drain_node"],
    }
    actions = suggestions.get(issue_type, ["restart_pod"])
    return [
        {
            "action": a,
            "resource": resource,
            "namespace": namespace,
            **_REMEDIATION_PLAYBOOKS.get(a, {"description": a, "risk": "unknown", "auto_approved": False}),
        }
        for a in actions
    ]


class RemediationEngine:
    """Execute remediation actions against the cluster."""

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
            logger.warning("K8s client unavailable for remediation: %s", exc)
            self._mock = True

    def execute(self, req: RemediationRequest) -> RemediationResult:
        logger.info(
            "Remediation: action=%s resource=%s/%s",
            req.action, req.namespace, req.resource_name
        )
        handler = getattr(self, f"_action_{req.action}", None)
        if handler is None:
            return RemediationResult(
                success=False,
                action=req.action,
                resource=f"{req.namespace}/{req.resource_name}",
                message=f"Unknown action: {req.action}",
            )
        return handler(req)

    def _action_restart_pod(self, req: RemediationRequest) -> RemediationResult:
        if self._mock:
            return RemediationResult(
                success=True,
                action="restart_pod",
                resource=f"{req.namespace}/{req.resource_name}",
                message=f"[MOCK] Pod {req.resource_name} restarted successfully.",
            )
        try:
            v1 = self._client.CoreV1Api()
            v1.delete_namespaced_pod(req.resource_name, req.namespace)
            return RemediationResult(
                success=True, action="restart_pod",
                resource=f"{req.namespace}/{req.resource_name}",
                message=f"Pod {req.resource_name} deleted and will be recreated.",
            )
        except Exception as exc:
            return RemediationResult(
                success=False, action="restart_pod",
                resource=f"{req.namespace}/{req.resource_name}",
                message=str(exc),
            )

    def _action_scale_deployment(self, req: RemediationRequest) -> RemediationResult:
        replicas = req.reason or "3"
        if self._mock:
            return RemediationResult(
                success=True,
                action="scale_deployment",
                resource=f"{req.namespace}/{req.resource_name}",
                message=f"[MOCK] Deployment {req.resource_name} scaled to {replicas} replicas.",
            )
        try:
            apps = self._client.AppsV1Api()
            body = {"spec": {"replicas": int(replicas)}}
            apps.patch_namespaced_deployment_scale(req.resource_name, req.namespace, body)
            return RemediationResult(
                success=True, action="scale_deployment",
                resource=f"{req.namespace}/{req.resource_name}",
                message=f"Deployment scaled to {replicas} replicas.",
            )
        except Exception as exc:
            return RemediationResult(
                success=False, action="scale_deployment",
                resource=f"{req.namespace}/{req.resource_name}",
                message=str(exc),
            )

    def _action_rollback_deployment(self, req: RemediationRequest) -> RemediationResult:
        return RemediationResult(
            success=True if self._mock else False,
            action="rollback_deployment",
            resource=f"{req.namespace}/{req.resource_name}",
            message=(
                f"[MOCK] Deployment {req.resource_name} rolled back to previous revision."
                if self._mock
                else "Rollback requires kubectl or Helm."
            ),
        )
