"""Alert processing and management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import Alert, AlertSeverity

logger = get_logger(__name__)
settings = get_settings()

_MOCK_ALERTS: list[dict[str, Any]] = [
    {
        "name": "PodCrashLooping",
        "severity": AlertSeverity.CRITICAL,
        "message": "Pod crash-loop-demo-abc has restarted 47 times in the last hour",
        "namespace": "default",
        "resource": "crash-loop-demo-abc",
    },
    {
        "name": "NodeMemoryPressure",
        "severity": AlertSeverity.WARNING,
        "message": "Node node-worker-2 memory usage at 87%, approaching limit",
        "namespace": "kube-system",
        "resource": "node-worker-2",
    },
    {
        "name": "DeploymentRolloutStuck",
        "severity": AlertSeverity.WARNING,
        "message": "Deployment worker has been progressing for over 10 minutes",
        "namespace": "default",
        "resource": "worker",
    },
    {
        "name": "HighErrorRate",
        "severity": AlertSeverity.CRITICAL,
        "message": "Error rate for api-gateway exceeded 5% (current: 12.3%)",
        "namespace": "default",
        "resource": "api-gateway",
    },
    {
        "name": "PrometheusTargetDown",
        "severity": AlertSeverity.WARNING,
        "message": "Prometheus scrape target node-exporter on node-worker-1 is down",
        "namespace": "monitoring",
        "resource": "node-exporter",
    },
]


class AlertManager:
    """Manage and process infrastructure alerts."""

    def __init__(self) -> None:
        self._active: dict[str, Alert] = {}
        self._resolved: list[Alert] = []
        self._seed_mock_alerts()

    def _seed_mock_alerts(self) -> None:
        now = datetime.utcnow()
        for i, raw in enumerate(_MOCK_ALERTS):
            alert = Alert(
                id=str(uuid.uuid4())[:8],
                name=raw["name"],
                severity=raw["severity"],
                message=raw["message"],
                namespace=raw["namespace"],
                resource=raw["resource"],
                timestamp=now - timedelta(minutes=i * 15 + 5),
                resolved=False,
            )
            self._active[alert.id] = alert

    def get_active_alerts(self) -> list[Alert]:
        return list(self._active.values())

    def add_alert(self, alert: Alert) -> None:
        self._active[alert.id] = alert
        logger.warning("Alert fired: [%s] %s", alert.severity.value.upper(), alert.name)

    def resolve_alert(self, alert_id: str) -> bool:
        if alert_id in self._active:
            alert = self._active.pop(alert_id)
            alert.resolved = True
            self._resolved.append(alert)
            logger.info("Alert resolved: %s", alert.name)
            return True
        return False

    def check_threshold_alerts(self, metrics: dict[str, float]) -> list[Alert]:
        new_alerts: list[Alert] = []

        def check(metric: str, warn: float, crit: float, label: str) -> None:
            val = metrics.get(metric, 0.0)
            if val >= crit:
                new_alerts.append(Alert(
                    id=str(uuid.uuid4())[:8],
                    name=f"High{label}",
                    severity=AlertSeverity.CRITICAL,
                    message=f"{label} usage critical: {val:.1f}% (threshold: {crit}%)",
                ))
            elif val >= warn:
                new_alerts.append(Alert(
                    id=str(uuid.uuid4())[:8],
                    name=f"High{label}Warning",
                    severity=AlertSeverity.WARNING,
                    message=f"{label} usage warning: {val:.1f}% (threshold: {warn}%)",
                ))

        check("cpu_pct", settings.cpu_warning_threshold, settings.cpu_critical_threshold, "CPU")
        check("memory_pct", settings.memory_warning_threshold, settings.memory_critical_threshold, "Memory")

        for alert in new_alerts:
            self.add_alert(alert)
        return new_alerts

    def get_alert_summary(self) -> dict[str, Any]:
        alerts = list(self._active.values())
        return {
            "total": len(alerts),
            "critical": sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL),
            "warning": sum(1 for a in alerts if a.severity == AlertSeverity.WARNING),
            "info": sum(1 for a in alerts if a.severity == AlertSeverity.INFO),
        }
