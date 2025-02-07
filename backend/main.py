"""InfraOS AI — FastAPI backend entry point."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ai.anomaly_detector import AnomalyDetector
from ai.nl_query import NLQueryEngine
from ai.remediation import RemediationEngine
from ai.root_cause import RootCauseAnalyzer
from integrations.grafana import GrafanaClient
from integrations.slack_notifier import SlackNotifier
from k8s.cluster_monitor import ClusterMonitor
from k8s.deployment_tracker import DeploymentTracker
from k8s.pod_manager import PodManager
from k8s.resource_analyzer import ResourceAnalyzer
from metrics.alert_manager import AlertManager
from metrics.metrics_store import MetricsStore
from metrics.prometheus_client import PrometheusClient
from shared.config import get_settings
from shared.logging import get_logger, setup_logging
from shared.models import (
    AnalysisRequest,
    IncidentAnalysisRequest,
    NLQueryRequest,
    RemediationRequest,
)

setup_logging()
logger = get_logger("infra-os.main")
settings = get_settings()

# Singletons initialised at startup
_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("InfraOS AI starting up (mock_mode=%s)", settings.k8s_mock_mode)
    _state["cluster_monitor"] = ClusterMonitor()
    _state["deployment_tracker"] = DeploymentTracker()
    _state["pod_manager"] = PodManager()
    _state["resource_analyzer"] = ResourceAnalyzer()
    _state["root_cause_analyzer"] = RootCauseAnalyzer()
    _state["anomaly_detector"] = AnomalyDetector()
    _state["remediation_engine"] = RemediationEngine()
    _state["nl_query_engine"] = NLQueryEngine()
    _state["prometheus_client"] = PrometheusClient()
    _state["alert_manager"] = AlertManager()
    _state["metrics_store"] = MetricsStore()
    _state["grafana_client"] = GrafanaClient()
    _state["slack_notifier"] = SlackNotifier()
    _state["ws_connections"]: list[WebSocket] = []
    logger.info("All services initialised")
    yield
    logger.info("InfraOS AI shutting down")


app = FastAPI(
    title="InfraOS AI",
    description="AI-powered DevOps Infrastructure Platform",
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "InfraOS AI", "version": settings.version}


# ---------------------------------------------------------------------------
# Kubernetes endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/k8s/cluster")
async def get_cluster() -> Any:
    monitor: ClusterMonitor = _state["cluster_monitor"]
    return monitor.get_cluster_overview()


@app.get("/api/v1/k8s/pods")
async def get_pods(namespace: str = "") -> Any:
    pm: PodManager = _state["pod_manager"]
    return pm.list_pods(namespace)


@app.get("/api/v1/k8s/deployments")
async def get_deployments(namespace: str = "") -> Any:
    dt: DeploymentTracker = _state["deployment_tracker"]
    return dt.list_deployments(namespace)


@app.get("/api/v1/k8s/events")
async def get_events() -> Any:
    monitor: ClusterMonitor = _state["cluster_monitor"]
    return monitor.get_events()


@app.post("/api/v1/k8s/analyze")
async def analyze_cluster(req: AnalysisRequest) -> dict[str, Any]:
    monitor: ClusterMonitor = _state["cluster_monitor"]
    overview = monitor.get_cluster_overview()
    pm: PodManager = _state["pod_manager"]
    pods = pm.list_pods()
    failing_pods = [p for p in pods if not p.ready]
    high_restart_pods = [p for p in pods if p.restarts > settings.pod_restart_warning_threshold]
    ra: ResourceAnalyzer = _state["resource_analyzer"]
    capacity = ra.get_cluster_capacity()
    return {
        "cluster_status": overview.status.value,
        "node_count": overview.node_count,
        "pod_count": overview.pod_count,
        "failing_pods": len(failing_pods),
        "high_restart_pods": len(high_restart_pods),
        "failing_pod_names": [p.name for p in failing_pods[:10]],
        "cluster_capacity": capacity,
        "recommendations": _generate_recommendations(failing_pods, high_restart_pods, capacity),
        "mock_mode": overview.mock_mode,
    }


def _generate_recommendations(failing: list[Any], high_restart: list[Any], capacity: dict[str, Any]) -> list[str]:
    recs: list[str] = []
    if failing:
        recs.append(f"{len(failing)} pod(s) are not ready. Check logs and events.")
    if high_restart:
        recs.append(f"{len(high_restart)} pod(s) have high restart counts — check for crash loops.")
    cpu = capacity.get("allocated_cpu_pct", 0)
    if cpu > 80:
        recs.append(f"Cluster CPU allocation is at {cpu}%. Consider adding nodes.")
    if not recs:
        recs.append("Cluster looks healthy. No immediate action required.")
    return recs


@app.post("/api/v1/k8s/nl-query")
async def nl_query(req: NLQueryRequest) -> Any:
    engine: NLQueryEngine = _state["nl_query_engine"]
    return await engine.query(req)


# ---------------------------------------------------------------------------
# Metrics & Prometheus
# ---------------------------------------------------------------------------

@app.get("/api/v1/metrics/prometheus")
async def get_prometheus_metrics(query: str = "up") -> Any:
    client: PrometheusClient = _state["prometheus_client"]
    return await client.query(query)


@app.get("/api/v1/metrics/snapshot")
async def get_metrics_snapshot() -> Any:
    store: MetricsStore = _state["metrics_store"]
    return store.generate_mock_snapshot()


@app.get("/api/v1/metrics/resources")
async def get_resource_usage() -> Any:
    ra: ResourceAnalyzer = _state["resource_analyzer"]
    return {
        "namespace_summary": ra.get_namespace_resource_summary(),
        "top_cpu": ra.get_top_consumers("cpu"),
        "top_memory": ra.get_top_consumers("memory"),
        "cluster_capacity": ra.get_cluster_capacity(),
    }


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@app.get("/api/v1/alerts")
async def get_alerts() -> Any:
    am: AlertManager = _state["alert_manager"]
    return {
        "alerts": am.get_active_alerts(),
        "summary": am.get_alert_summary(),
    }


# ---------------------------------------------------------------------------
# Remediation
# ---------------------------------------------------------------------------

@app.post("/api/v1/remediate")
async def remediate(req: RemediationRequest) -> Any:
    engine: RemediationEngine = _state["remediation_engine"]
    result = engine.execute(req)
    if result.success:
        slack: SlackNotifier = _state["slack_notifier"]
        await slack.send_message(
            f"Remediation executed: {req.action} on {req.namespace}/{req.resource_name}"
        )
    return result


# ---------------------------------------------------------------------------
# Incident Analysis
# ---------------------------------------------------------------------------

@app.post("/api/v1/incident/analyze")
async def analyze_incident(req: IncidentAnalysisRequest) -> Any:
    analyzer: RootCauseAnalyzer = _state["root_cause_analyzer"]
    rca = await analyzer.analyze(req)
    slack: SlackNotifier = _state["slack_notifier"]
    await slack.send_message(
        f"Incident RCA completed: {rca.root_cause[:100]} (confidence: {rca.confidence:.0%})"
    )
    return rca


# ---------------------------------------------------------------------------
# Grafana
# ---------------------------------------------------------------------------

@app.get("/api/v1/grafana/dashboards")
async def get_grafana_dashboards() -> Any:
    client: GrafanaClient = _state["grafana_client"]
    return await client.get_dashboards()


# ---------------------------------------------------------------------------
# WebSocket — real-time metrics stream
# ---------------------------------------------------------------------------

@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    await websocket.accept()
    connections: list[WebSocket] = _state["ws_connections"]
    connections.append(websocket)
    store: MetricsStore = _state["metrics_store"]
    logger.info("WebSocket client connected (%d total)", len(connections))
    try:
        while True:
            snapshot = store.generate_mock_snapshot()
            await websocket.send_text(json.dumps(snapshot, default=str))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        connections.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(connections))
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        if websocket in connections:
            connections.remove(websocket)
