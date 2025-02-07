# InfraOS AI API Reference

Base URL: `http://localhost:8000`

## Health

### GET /health
```json
{"status": "ok", "service": "InfraOS AI", "mock_mode": true}
```

## Kubernetes

### GET /api/v1/k8s/cluster
Cluster overview: node count, pod count, health status.

### GET /api/v1/k8s/pods
List all pods with status, namespace, restarts, age.

### GET /api/v1/k8s/deployments
List deployments with ready/desired replica counts.

### GET /api/v1/k8s/events
Recent cluster events (warnings and normal).

### POST /api/v1/k8s/analyze
AI analysis of current cluster state.

**Request:**
```json
{"focus": "failing pods"}
```

**Response:**
```json
{
  "analysis": "3 pods in CrashLoopBackOff in namespace production...",
  "root_cause": "OOMKilled — memory limit too low",
  "recommendation": "Increase memory limit to 512Mi"
}
```

### POST /api/v1/k8s/nl-query
```json
{"query": "why is my nginx pod restarting?"}
```

## Metrics

### GET /api/v1/metrics/prometheus
Query Prometheus directly.

**Params:** `query` (PromQL string), `start`, `end`, `step`

### GET /api/v1/alerts
Current active alerts.

## Remediation

### POST /api/v1/remediate
```json
{
  "action": "restart_pod",
  "namespace": "production",
  "pod_name": "nginx-abc123"
}
```

## WebSocket

### WS /ws/metrics
Real-time metrics stream every 5 seconds.
