"""Natural language to Kubernetes query translation."""

from __future__ import annotations

import re
from typing import Any

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import NLQueryRequest, NLQueryResponse

logger = get_logger(__name__)
settings = get_settings()

_PATTERN_MAP: list[dict[str, Any]] = [
    {
        "patterns": [r"why.*(pod|container).*crash", r"crash.*loop", r"crashloopbackoff"],
        "kubectl": "kubectl get pods -A | grep -E 'CrashLoop|Error' && kubectl describe pod <pod-name> -n <namespace>",
        "explanation": "Shows pods in crash loop state and describes the failing pod for root cause details.",
        "suggestions": [
            "Check logs: kubectl logs <pod> --previous",
            "Describe pod for events: kubectl describe pod <pod>",
            "Check resource limits: kubectl get pod <pod> -o yaml",
        ],
        "mock_result": "NAME                  READY   STATUS             RESTARTS\ncrash-loop-demo-abc   0/1     CrashLoopBackOff   47       \nworker-xyz            1/1     Running            8",
    },
    {
        "patterns": [r"node.*status", r"node.*health", r"which node"],
        "kubectl": "kubectl get nodes -o wide",
        "explanation": "Lists all cluster nodes with their status, roles, IP addresses, and Kubernetes version.",
        "suggestions": [
            "Describe a node: kubectl describe node <node-name>",
            "Check node resources: kubectl top nodes",
        ],
        "mock_result": "NAME                STATUS   ROLES           AGE   VERSION\nnode-control-plane  Ready    control-plane   15d   v1.29.2\nnode-worker-1       Ready    worker          15d   v1.29.2\nnode-worker-2       Ready    worker          15d   v1.29.2",
    },
    {
        "patterns": [r"memory.*usage", r"out of memory", r"oom"],
        "kubectl": "kubectl top pods -A --sort-by=memory | head -20",
        "explanation": "Shows top memory-consuming pods across all namespaces, sorted by memory usage.",
        "suggestions": [
            "Set memory limits in pod spec",
            "Enable VPA (Vertical Pod Autoscaler)",
            "Check for memory leaks in application",
        ],
        "mock_result": "NAMESPACE   NAME              CPU(cores)   MEMORY(bytes)\ndefault     worker-abc        450m         512Mi\ndefault     api-gateway-xyz   120m         256Mi\nmonitoring  prometheus-001    80m          1024Mi",
    },
    {
        "patterns": [r"cpu.*usage", r"cpu.*high", r"cpu.*spike"],
        "kubectl": "kubectl top pods -A --sort-by=cpu | head -20",
        "explanation": "Shows top CPU-consuming pods, helpful for identifying resource bottlenecks.",
        "suggestions": [
            "Check HPA configuration",
            "Review pod CPU limits and requests",
            "Consider horizontal scaling",
        ],
        "mock_result": "NAMESPACE   NAME              CPU(cores)   MEMORY(bytes)\ndefault     worker-abc        950m         256Mi\ndefault     api-gateway-xyz   720m         128Mi\ndefault     auth-service-def  380m         96Mi",
    },
    {
        "patterns": [r"deployment.*status", r"rollout.*status", r"deploy.*health"],
        "kubectl": "kubectl get deployments -A",
        "explanation": "Shows all deployments with their desired vs ready replica counts.",
        "suggestions": [
            "Check rollout: kubectl rollout status deployment/<name>",
            "View history: kubectl rollout history deployment/<name>",
        ],
        "mock_result": "NAMESPACE   NAME               READY   UP-TO-DATE   AVAILABLE\ndefault     api-gateway        3/3     3            3\ndefault     auth-service       2/2     2            2\ndefault     worker             0/2     1            0 ← DEGRADED",
    },
    {
        "patterns": [r"pending.*pod", r"pod.*stuck", r"pod.*not.*start"],
        "kubectl": "kubectl get pods -A --field-selector=status.phase=Pending",
        "explanation": "Lists pods stuck in Pending state, typically caused by resource constraints or scheduling issues.",
        "suggestions": [
            "Describe pod: kubectl describe pod <pod> for scheduling failure reason",
            "Check node resources: kubectl describe nodes",
            "Review resource requests in pod spec",
        ],
        "mock_result": "NAMESPACE   NAME           READY   STATUS    RESTARTS   AGE\ndefault     heavy-job-abc  0/1     Pending   0          15m\n\nWarning: Insufficient CPU on all nodes",
    },
    {
        "patterns": [r"service.*not.*reachab", r"service.*down", r"endpoint"],
        "kubectl": "kubectl get endpoints -A | grep -v '<none>'",
        "explanation": "Shows service endpoints to verify that services have healthy backing pods.",
        "suggestions": [
            "Check service selector matches pod labels",
            "Verify pod is Running and Ready",
            "Test DNS: kubectl exec <pod> -- nslookup <service>",
        ],
        "mock_result": "NAMESPACE   NAME            ENDPOINTS\ndefault     api-gateway     10.0.0.5:8080,10.0.0.6:8080\ndefault     auth-service    10.0.0.7:3000\ndefault     frontend        <none> ← NO ENDPOINTS",
    },
]

_DEFAULT_RESPONSE = NLQueryResponse(
    query="",
    kubectl_command="kubectl get all -A",
    explanation="Shows all Kubernetes resources across all namespaces.",
    result="Use a more specific query to get detailed information.",
    suggestions=[
        "Try: 'why is my pod crashing?'",
        "Try: 'show node status'",
        "Try: 'which pods are using most memory?'",
    ],
)


def _match_pattern(query: str) -> dict[str, Any] | None:
    q = query.lower()
    for entry in _PATTERN_MAP:
        for pat in entry["patterns"]:
            if re.search(pat, q):
                return entry
    return None


async def _ai_nl_query(query: str, namespace: str) -> NLQueryResponse:
    if settings.openai_api_key:
        try:
            return await _openai_nl_query(query, namespace)
        except Exception as exc:
            logger.warning("OpenAI NL query failed: %s", exc)
    match = _match_pattern(query)
    if match:
        return NLQueryResponse(
            query=query,
            kubectl_command=match["kubectl"],
            explanation=match["explanation"],
            result=match["mock_result"],
            suggestions=match.get("suggestions", []),
        )
    resp = _DEFAULT_RESPONSE.model_copy()
    resp.query = query
    return resp


async def _openai_nl_query(query: str, namespace: str) -> NLQueryResponse:
    import openai  # type: ignore[import]
    aclient = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    prompt = (
        f"You are a Kubernetes expert. Convert this question to a kubectl command and explain it.\n"
        f"Question: {query}\nNamespace context: {namespace}\n\n"
        "Respond with JSON: {\"kubectl\": \"...\", \"explanation\": \"...\", \"suggestions\": [\"...\"]}"
    )
    response = await aclient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    import json
    data = json.loads(response.choices[0].message.content or "{}")
    return NLQueryResponse(
        query=query,
        kubectl_command=data.get("kubectl", "kubectl get all"),
        explanation=data.get("explanation", ""),
        result="[Run command against your cluster to see results]",
        suggestions=data.get("suggestions", []),
    )


class NLQueryEngine:
    """Convert natural language questions to kubectl commands."""

    async def query(self, req: NLQueryRequest) -> NLQueryResponse:
        logger.info("NL query: %s", req.query)
        return await _ai_nl_query(req.query, req.namespace)
