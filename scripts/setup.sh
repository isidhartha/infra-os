#!/usr/bin/env bash
set -euo pipefail

echo "=== InfraOS AI Setup ==="

python3 -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'" || {
    echo "ERROR: Python 3.11+ required"
    exit 1
}

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env — set K8S_MOCK_MODE=true for development without a cluster"
fi

mkdir -p config/grafana/dashboards

cd backend
pip install -r requirements.txt

echo ""
echo "Start with: docker-compose up --build"
echo "Dashboard: http://localhost:3000"
echo "Prometheus: http://localhost:9090"
echo "Grafana:    http://localhost:3001 (admin/admin)"
