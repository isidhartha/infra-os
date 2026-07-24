# InfraOS AI

[![Discussions](https://img.shields.io/github/discussions/isidhartha/infra-os)](https://github.com/isidhartha/infra-os/discussions)

## Demo

![Demo Animation](docs/images/demo.gif)

### Screenshots

| Desktop Dashboard | Feature View | Mobile View |
|------------------|--------------|--------------|
| ![Desktop](docs/images/screenshot_desktop.png) | ![Feature](docs/images/screenshot_feature.png) | ![Mobile](docs/images/screenshot_mobile.png) |


I was on-call for a service once and got paged at 2am for a Kubernetes cluster that was falling apart in three different ways simultaneously. I spent 45 minutes running `kubectl` commands to understand what was happening before I could even start fixing it. InfraOS AI is my answer to that problem.

It's a DevOps operations platform that connects to your Kubernetes cluster, pulls in everything that's happening — pods, deployments, resource usage, events, Prometheus metrics — and gives you an AI layer to make sense of it all. You can ask "why is this pod crashing?" in plain English and get a real answer, not a wall of log output to parse yourself.

---

## What it does

**Cluster monitoring** — Live view of your nodes, pods, deployments, and services. Health status, restart counts, resource requests vs. limits. Everything in one dashboard rather than spread across ten kubectl commands.

**Natural language queries** — Ask questions about your cluster in plain English. "Which pods have restarted more than 5 times in the last hour?" or "What's consuming the most memory in the production namespace?" — it translates these into the right queries and gives you the answer.

**Root cause analysis** — When something breaks, tell it what happened and it traces back through events, logs, and metrics to figure out why. It's not magic — it looks at the same signals you'd look at manually, just faster and with an AI to synthesize them.

**Anomaly detection** — Watches your metrics over time and flags things that look unusual before they become incidents. High memory growth rate, unusual request patterns, CPU spikes that don't match your normal traffic pattern.

**Automated remediation** — For common problems it can take action directly: restart a crashed pod, scale a deployment up or down, cordon a misbehaving node. Every action gets logged and can trigger a Slack notification.

**Prometheus and Grafana** — Built-in integration with both. Grafana runs as part of the Docker Compose stack. Prometheus scrapes whatever you point it at.

**Mock mode** — No Kubernetes cluster? No problem. Set `K8S_MOCK_MODE=true` and the platform generates realistic fake cluster data. Useful for exploring the UI, testing your alerting rules, or demoing to someone.

---

## How to run it

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git
- Redis (`redis-server`)
- PostgreSQL 13+ with database `infraos` created
- Ollama (optional, for running without any API key — https://ollama.com)
- Prometheus (optional) — https://prometheus.io/download/
- Grafana (optional) — https://grafana.com/grafana/download

### Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/isidhartha/infra-os
cd infra-os

# 2. Create virtual environment
# Windows:
python -m venv venv
venv\Scripts\activate
# Mac/Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env
# Open .env and fill in at least one AI provider key
# OR set AI_PROVIDER=ollama to run without any API key
# K8S_MOCK_MODE=true is set by default (no real cluster needed)

# 5. Start services
# Redis (in a terminal):
redis-server
# PostgreSQL must be running — create the database once:
# psql -U postgres -c "CREATE DATABASE infraos;"

# 6. Run the backend
cd backend
uvicorn main:app --reload --port 8005

# 7. Run the frontend (in a new terminal, from project root)
cd frontend
npm install
npm run dev -- --port 3005
```

**Dashboard**: http://localhost:3005  
**API docs**: http://localhost:8005/docs

| Service | URL |
|---|---|
| InfraOS Dashboard | http://localhost:3005 |
| API | http://localhost:8005 |
| Prometheus (if running) | http://localhost:9090 |
| Grafana (if running) | http://localhost:3001 |

---

## Connecting a real cluster

Set `K8S_MOCK_MODE=false` in `.env` and mount your kubeconfig:

```yaml
# In docker-compose.yml, under the backend service:
volumes:
  - ~/.kube:/root/.kube:ro
```

The backend uses the standard kubeconfig format. Whatever `kubectl` can reach, InfraOS can reach.

---

## API

Swagger UI at `http://localhost:8000/docs`.

```
GET  /api/v1/k8s/cluster         — Cluster overview
GET  /api/v1/k8s/pods            — List pods (filter by namespace)
GET  /api/v1/k8s/deployments     — List deployments
POST /api/v1/k8s/nl-query        — Natural language query
POST /api/v1/incident/analyze    — Root cause analysis
POST /api/v1/remediate           — Execute a remediation action
GET  /api/v1/alerts              — Active alerts
GET  /api/v1/metrics/snapshot    — Current metrics snapshot
WS   /ws/metrics                 — Real-time metrics stream
```

---

## Configuration

| Variable | Description | Default |
|------------------|--------------|--------------|
| `OPENAI_API_KEY` | For AI analysis and NL queries | — |
| `K8S_MOCK_MODE` | Run with fake cluster data | `true` |
| `PROMETHEUS_URL` | Prometheus endpoint | `http://prometheus:9090` |
| `GRAFANA_URL` | Grafana endpoint | `http://grafana:3000` |
| `SLACK_WEBHOOK_URL` | Slack notifications for remediations | — |
| `POD_RESTART_WARNING_THRESHOLD` | Alert when a pod restarts this many times | `5` |

---

## Free local LLM option (no API key needed)

InfraOS AI can run its AI features entirely on your machine using [Ollama](https://ollama.com) — no OpenAI account or API key required.

**1. Install Ollama**

Download from https://ollama.com and install it. Then pull a model:

```bash
ollama pull llama3.2
```

**2. Set the provider in `.env`**

```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Leave `OPENAI_API_KEY` blank. The backend will route all AI calls to your local Ollama instance instead.

**3. Start Ollama and then the stack**

```bash
ollama serve          # keep this running in one terminal
docker-compose up --build
```

If you're running Ollama on your host machine and the backend inside Docker, the compose file already sets `OLLAMA_BASE_URL=http://host.docker.internal:11434` so the container can reach it. On Linux, you may need to use your host's LAN IP instead of `host.docker.internal`.

**Switching back to OpenAI** is just changing `LLM_PROVIDER=openai` in `.env` and restarting the backend.

---

## License

MIT. Run it on your own infrastructure, fork it, build on top of it.
