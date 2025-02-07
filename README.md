# InfraOS AI — AI DevOps Infrastructure Platform

> Kubernetes monitoring, AI root-cause analysis, predictive alerts, and automated remediation — your AI-powered DevOps copilot.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

## Features

- [x] Kubernetes cluster monitoring (pods, nodes, services)
- [x] Deployment rollout tracking
- [x] AI root-cause analysis ("why is my pod crashing?")
- [x] Natural language K8s queries
- [x] Prometheus metrics integration
- [x] Grafana dashboard integration
- [x] Predictive anomaly detection
- [x] Automated remediation workflows
- [x] Slack / webhook alerting
- [x] Mock mode (works without a real cluster)

## Architecture

```mermaid
graph TD
    A[Kubernetes Cluster] -->|Metrics| B[Prometheus]
    B -->|Query| C[InfraOS Backend]
    A -->|Events/Logs| C
    C --> D[AI Analysis Engine]
    D --> E[Root Cause Analyzer]
    D --> F[Anomaly Detector]
    D --> G[Remediation Engine]
    C --> H[Grafana Dashboards]
    C --> I[Web Dashboard]
    G --> J[Auto-remediation Actions]
    C --> K[Slack Alerts]
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11+ |
| K8s Client | kubernetes-python |
| Metrics | Prometheus + prometheus-client |
| Visualization | Grafana (official image) |
| AI | OpenAI GPT-4 / Anthropic Claude |
| ML | scikit-learn (anomaly detection) |
| Frontend | React 18, Recharts, Tailwind |

## Quick Start

```bash
git clone https://github.com/yourusername/infra-os
cd infra-os
cp .env.example .env
# Set K8S_MOCK_MODE=true if you don't have a cluster
docker-compose up --build
```

Open `http://localhost:3000` for the dashboard, `http://localhost:3001` for Grafana, `http://localhost:9090` for Prometheus.

## Mock Mode

Set `K8S_MOCK_MODE=true` in `.env` to run with realistic fake cluster data — no Kubernetes cluster required.

## License

MIT — see [LICENSE](LICENSE).
