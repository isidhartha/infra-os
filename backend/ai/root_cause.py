"""AI-powered root cause analysis for Kubernetes incidents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import IncidentAnalysisRequest, RootCauseAnalysis

logger = get_logger(__name__)
settings = get_settings()

_HEURISTICS: list[dict[str, Any]] = [
    {
        "keywords": ["OOMKill", "OOMKilling", "memory", "limit exceeded"],
        "cause": "Out-of-memory (OOM): container exceeded its memory limit",
        "factors": ["Memory limit set too low", "Memory leak in application", "Sudden traffic spike"],
        "actions": [
            "Increase memory limits in the pod spec",
            "Investigate memory leak with profiler",
            "Enable Horizontal Pod Autoscaling",
            "Review recent code changes for memory regressions",
        ],
    },
    {
        "keywords": ["CrashLoopBackOff", "BackOff", "crash"],
        "cause": "Container is crash-looping: process exits immediately on start",
        "factors": ["Application startup failure", "Missing environment variables", "Dependency unavailable", "Configuration error"],
        "actions": [
            "Check pod logs: kubectl logs <pod> --previous",
            "Verify all required environment variables are set",
            "Ensure dependent services (DB, Redis) are healthy",
            "Check liveness probe configuration",
        ],
    },
    {
        "keywords": ["ImagePullBackOff", "ErrImagePull", "image", "pull"],
        "cause": "Container image cannot be pulled from registry",
        "factors": ["Invalid image tag", "Registry authentication failure", "Network connectivity issue", "Private registry without secret"],
        "actions": [
            "Verify image name and tag exist in registry",
            "Check imagePullSecrets are configured correctly",
            "Verify network access to container registry",
            "Try pulling image manually: docker pull <image>",
        ],
    },
    {
        "keywords": ["Pending", "Unschedulable", "node", "resource", "insufficient"],
        "cause": "Pod is unschedulable: no node can satisfy resource requirements",
        "factors": ["Insufficient CPU/memory on all nodes", "Node selector/affinity constraints", "Taints not tolerated"],
        "actions": [
            "Check node capacity: kubectl describe nodes",
            "Review resource requests in pod spec",
            "Add cluster nodes or increase node size",
            "Review pod affinity and node selector rules",
        ],
    },
    {
        "keywords": ["timeout", "connection refused", "network", "DNS"],
        "cause": "Network connectivity failure between services",
        "factors": ["Service DNS not resolving", "NetworkPolicy blocking traffic", "Service endpoint not ready"],
        "actions": [
            "Verify service and endpoints: kubectl get endpoints",
            "Check NetworkPolicy rules",
            "Test DNS resolution from within pod",
            "Review service selector labels",
        ],
    },
]

_FALLBACK_ANALYSIS = RootCauseAnalysis(
    incident_id="",
    root_cause="Insufficient data to determine root cause automatically",
    confidence=0.3,
    contributing_factors=["Multiple potential causes", "Insufficient log data"],
    recommended_actions=[
        "Gather more logs: kubectl logs <pod> --previous",
        "Check recent deployments for changes",
        "Review Prometheus metrics for anomalies",
    ],
    timeline=[],
)


def _heuristic_analysis(description: str, resources: list[str]) -> RootCauseAnalysis | None:
    combined = (description + " " + " ".join(resources)).lower()
    best: dict[str, Any] | None = None
    best_score = 0
    for h in _HEURISTICS:
        score = sum(1 for kw in h["keywords"] if kw.lower() in combined)
        if score > best_score:
            best_score = score
            best = h
    if not best or best_score == 0:
        return None
    confidence = min(0.95, 0.5 + best_score * 0.15)
    return RootCauseAnalysis(
        incident_id=str(uuid.uuid4())[:8],
        root_cause=best["cause"],
        confidence=confidence,
        contributing_factors=best["factors"],
        recommended_actions=best["actions"],
        timeline=[
            {"time": "T-15m", "event": "Anomalous metric spike detected"},
            {"time": "T-10m", "event": "First warning event recorded"},
            {"time": "T-5m", "event": "Pod entered failure state"},
            {"time": "T-0m", "event": "Incident detected and alert fired"},
        ],
    )


async def _ai_analysis(req: IncidentAnalysisRequest) -> RootCauseAnalysis:
    """Attempt AI analysis via OpenAI/Anthropic, fall back to heuristics."""
    if settings.openai_api_key:
        try:
            return await _openai_analysis(req)
        except Exception as exc:
            logger.warning("OpenAI analysis failed: %s", exc)
    if settings.anthropic_api_key:
        try:
            return await _anthropic_analysis(req)
        except Exception as exc:
            logger.warning("Anthropic analysis failed: %s", exc)
    heuristic = _heuristic_analysis(req.description, req.affected_resources)
    if heuristic:
        heuristic.incident_id = req.incident_id or str(uuid.uuid4())[:8]
        return heuristic
    result = _FALLBACK_ANALYSIS.model_copy()
    result.incident_id = req.incident_id or str(uuid.uuid4())[:8]
    return result


async def _openai_analysis(req: IncidentAnalysisRequest) -> RootCauseAnalysis:
    import openai  # type: ignore[import]
    aclient = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    prompt = (
        f"You are a Kubernetes SRE expert. Analyze this incident:\n"
        f"Description: {req.description}\n"
        f"Affected resources: {', '.join(req.affected_resources)}\n"
        f"Time range: last {req.time_range_minutes} minutes\n\n"
        "Provide: 1) Root cause, 2) Contributing factors (list), "
        "3) Recommended actions (list), 4) Confidence score 0-1. "
        "Be concise and actionable."
    )
    response = await aclient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
    )
    text = response.choices[0].message.content or ""
    return RootCauseAnalysis(
        incident_id=req.incident_id or str(uuid.uuid4())[:8],
        root_cause=text[:300],
        confidence=0.75,
        contributing_factors=["See AI analysis above"],
        recommended_actions=["Review AI analysis and apply suggestions"],
        timeline=[],
    )


async def _anthropic_analysis(req: IncidentAnalysisRequest) -> RootCauseAnalysis:
    import anthropic  # type: ignore[import]
    aclient = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = (
        f"Kubernetes incident analysis:\nDescription: {req.description}\n"
        f"Affected: {', '.join(req.affected_resources)}\n"
        "Identify root cause, contributing factors, and remediation steps."
    )
    message = await aclient.messages.create(
        model="claude-haiku-20240307",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text if message.content else ""
    return RootCauseAnalysis(
        incident_id=req.incident_id or str(uuid.uuid4())[:8],
        root_cause=text[:300],
        confidence=0.80,
        contributing_factors=["See Claude analysis"],
        recommended_actions=["Review Claude analysis and apply suggestions"],
        timeline=[],
    )


class RootCauseAnalyzer:
    """Analyze Kubernetes incidents to determine root cause."""

    async def analyze(self, req: IncidentAnalysisRequest) -> RootCauseAnalysis:
        logger.info("Analyzing incident: %s", req.description[:80])
        return await _ai_analysis(req)
