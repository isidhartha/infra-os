"""Shared Pydantic models for InfraOS AI."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class PodPhase(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PodInfo(BaseModel):
    name: str
    namespace: str
    phase: PodPhase
    ready: bool
    restarts: int
    node: str
    age: str
    cpu_usage: str = "N/A"
    memory_usage: str = "N/A"
    labels: dict[str, str] = Field(default_factory=dict)


class NodeInfo(BaseModel):
    name: str
    status: HealthStatus
    roles: list[str]
    cpu_capacity: str
    memory_capacity: str
    cpu_usage: str = "N/A"
    memory_usage: str = "N/A"
    pod_count: int = 0
    age: str


class DeploymentInfo(BaseModel):
    name: str
    namespace: str
    desired: int
    ready: int
    available: int
    updated: int
    strategy: str
    age: str
    image: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN


class ClusterOverview(BaseModel):
    name: str
    version: str
    status: HealthStatus
    node_count: int
    pod_count: int
    deployment_count: int
    namespace_count: int
    nodes: list[NodeInfo]
    mock_mode: bool = False


class ClusterEvent(BaseModel):
    name: str
    namespace: str
    reason: str
    message: str
    kind: str
    count: int
    event_type: str
    first_time: str
    last_time: str


class Alert(BaseModel):
    id: str
    name: str
    severity: AlertSeverity
    message: str
    namespace: str = ""
    resource: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    labels: dict[str, str] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)
    focus: str = "general"


class NLQueryRequest(BaseModel):
    query: str
    namespace: str = "default"


class NLQueryResponse(BaseModel):
    query: str
    kubectl_command: str
    explanation: str
    result: str
    suggestions: list[str] = Field(default_factory=list)


class RemediationRequest(BaseModel):
    resource_type: str
    resource_name: str
    namespace: str
    action: str
    reason: str = ""


class RemediationResult(BaseModel):
    success: bool
    action: str
    resource: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IncidentAnalysisRequest(BaseModel):
    incident_id: str = ""
    description: str
    affected_resources: list[str] = Field(default_factory=list)
    time_range_minutes: int = 30


class RootCauseAnalysis(BaseModel):
    incident_id: str
    root_cause: str
    confidence: float
    contributing_factors: list[str]
    recommended_actions: list[str]
    timeline: list[dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricSample(BaseModel):
    metric: dict[str, str]
    value: float
    timestamp: float


class PrometheusQueryResult(BaseModel):
    query: str
    result_type: str
    samples: list[MetricSample]
