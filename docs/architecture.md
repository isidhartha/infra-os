# InfraOS AI Architecture

## Overview

InfraOS AI connects to Kubernetes clusters and Prometheus, applies AI analysis, and surfaces insights through a web dashboard.

## Data Flow

```
Kubernetes API → cluster_monitor.py → Backend
Prometheus API → prometheus_client.py → Backend
Backend → AI Analysis Engine → Insights
Backend → WebSocket → Dashboard
```

## Kubernetes Integration

Uses the official `kubernetes` Python client:
- `ClusterMonitor` reads pod, node, service, and event data
- `DeploymentTracker` watches rollout status
- `PodManager` handles restart and scale operations
- `ResourceAnalyzer` calculates CPU/memory utilization

**Mock Mode**: When `K8S_MOCK_MODE=true`, all K8s functions return realistic fake data, enabling development without a cluster.

## AI Analysis

### Root Cause Analysis
1. Collect: pods in CrashLoopBackOff, OOMKilled events, recent log errors
2. Summarize context to AI
3. AI returns probable root cause + recommended fix

### Anomaly Detection
- scikit-learn IsolationForest on metric time series
- Sliding window of 60 data points
- Alert when anomaly score exceeds threshold

### Natural Language Queries
Convert plain English to kubectl-equivalent API calls:
- "why is nginx crashing?" → get pod events + logs → AI explains

## Metrics Pipeline

```
Prometheus scrape → prometheus_client.py → metrics_store.py (Redis cache)
                                        → anomaly_detector.py
                                        → alert_manager.py → Slack
```

## Grafana Integration

- Pre-configured dashboards provisioned via `config/grafana/dashboards/`
- InfraOS backend also exposes `/api/v1/metrics/prometheus` for custom panels
