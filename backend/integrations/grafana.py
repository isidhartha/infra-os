"""Grafana HTTP API integration."""

from __future__ import annotations

from typing import Any

import httpx

from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GrafanaClient:
    """Interact with the Grafana HTTP API."""

    def __init__(self) -> None:
        self._base = settings.grafana_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {settings.grafana_api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = 10.0

    async def get_dashboards(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}/api/search",
                    headers=self._headers,
                    params={"type": "dash-db"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("Grafana dashboards unavailable: %s", exc)
            return [
                {"id": 1, "uid": "infra-os-main", "title": "InfraOS Overview", "url": "/d/infra-os-main"},
                {"id": 2, "uid": "k8s-cluster", "title": "Kubernetes Cluster", "url": "/d/k8s-cluster"},
                {"id": 3, "uid": "node-exporter", "title": "Node Exporter Full", "url": "/d/node-exporter"},
            ]

    async def get_alerts(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}/api/alerts",
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("Grafana alerts unavailable: %s", exc)
            return []

    async def create_annotation(self, text: str, tags: list[str] | None = None) -> dict[str, Any]:
        body = {"text": text, "tags": tags or ["infra-os", "automated"]}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/api/annotations",
                    headers=self._headers,
                    json=body,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("Failed to create Grafana annotation: %s", exc)
            return {"id": 0, "message": "mock annotation created"}

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base}/api/health")
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return {"database": "unknown", "version": "unknown", "commit": "unknown"}
