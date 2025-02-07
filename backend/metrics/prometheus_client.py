"""Prometheus HTTP API client for querying metrics."""

from __future__ import annotations

import time
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import MetricSample, PrometheusQueryResult

logger = get_logger(__name__)
settings = get_settings()

_MOCK_QUERIES: dict[str, list[dict[str, Any]]] = {
    "up": [
        {"metric": {"__name__": "up", "job": "prometheus"}, "value": [time.time(), "1"]},
        {"metric": {"__name__": "up", "job": "node-exporter"}, "value": [time.time(), "1"]},
        {"metric": {"__name__": "up", "job": "kube-state-metrics"}, "value": [time.time(), "1"]},
    ],
    "node_cpu": [
        {"metric": {"__name__": "node_cpu_seconds_total", "cpu": "0", "mode": "idle"}, "value": [time.time(), "0.65"]},
        {"metric": {"__name__": "node_cpu_seconds_total", "cpu": "1", "mode": "idle"}, "value": [time.time(), "0.72"]},
    ],
    "node_memory": [
        {"metric": {"__name__": "node_memory_MemAvailable_bytes"}, "value": [time.time(), "8589934592"]},
        {"metric": {"__name__": "node_memory_MemTotal_bytes"}, "value": [time.time(), "17179869184"]},
    ],
}


def _parse_samples(data: list[dict[str, Any]]) -> list[MetricSample]:
    samples = []
    for item in data:
        ts, val = item.get("value", [time.time(), "0"])
        try:
            samples.append(
                MetricSample(
                    metric=item.get("metric", {}),
                    value=float(val),
                    timestamp=float(ts),
                )
            )
        except (ValueError, TypeError):
            pass
    return samples


class PrometheusClient:
    """Query Prometheus HTTP API with mock fallback."""

    def __init__(self) -> None:
        self._base = settings.prometheus_url.rstrip("/")
        self._timeout = 10.0

    async def query(self, promql: str) -> PrometheusQueryResult:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}/api/v1/query",
                    params={"query": promql},
                )
                resp.raise_for_status()
                body = resp.json()
                result_type = body["data"]["resultType"]
                raw = body["data"]["result"]
                return PrometheusQueryResult(
                    query=promql,
                    result_type=result_type,
                    samples=_parse_samples(raw),
                )
        except Exception as exc:
            logger.warning("Prometheus query failed, returning mock: %s", exc)
            return self._mock_query(promql)

    def _mock_query(self, promql: str) -> PrometheusQueryResult:
        key = "up"
        for k in _MOCK_QUERIES:
            if k in promql.lower():
                key = k
                break
        raw = _MOCK_QUERIES.get(key, _MOCK_QUERIES["up"])
        return PrometheusQueryResult(
            query=promql,
            result_type="vector",
            samples=_parse_samples(raw),
        )

    async def query_range(
        self,
        promql: str,
        start: float,
        end: float,
        step: str = "60s",
    ) -> PrometheusQueryResult:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}/api/v1/query_range",
                    params={"query": promql, "start": start, "end": end, "step": step},
                )
                resp.raise_for_status()
                body = resp.json()
                raw = body["data"]["result"]
                samples = []
                for series in raw:
                    for ts, val in series.get("values", []):
                        try:
                            samples.append(MetricSample(
                                metric=series.get("metric", {}),
                                value=float(val),
                                timestamp=float(ts),
                            ))
                        except (ValueError, TypeError):
                            pass
                return PrometheusQueryResult(
                    query=promql, result_type="matrix", samples=samples
                )
        except Exception as exc:
            logger.warning("Prometheus range query failed: %s", exc)
            return self._mock_query(promql)

    async def get_targets(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base}/api/v1/targets")
                resp.raise_for_status()
                return resp.json().get("data", {}).get("activeTargets", [])
        except Exception:
            return [
                {"job": "prometheus", "health": "up", "scrapeUrl": f"{self._base}/metrics"},
                {"job": "node-exporter", "health": "up", "scrapeUrl": "http://node-exporter:9100/metrics"},
                {"job": "kube-state-metrics", "health": "up", "scrapeUrl": "http://kube-state-metrics:8080/metrics"},
            ]
