"""Slack alert notifications via webhook."""

from __future__ import annotations

from typing import Any

import httpx

from shared.config import get_settings
from shared.logging import get_logger
from shared.models import Alert, AlertSeverity

logger = get_logger(__name__)
settings = get_settings()

_SEVERITY_EMOJI = {
    AlertSeverity.CRITICAL: ":red_circle:",
    AlertSeverity.WARNING: ":warning:",
    AlertSeverity.INFO: ":information_source:",
}
_SEVERITY_COLOR = {
    AlertSeverity.CRITICAL: "#FF0000",
    AlertSeverity.WARNING: "#FFA500",
    AlertSeverity.INFO: "#36A64F",
}


def _build_payload(alert: Alert, extra: str = "") -> dict[str, Any]:
    emoji = _SEVERITY_EMOJI.get(alert.severity, ":bell:")
    color = _SEVERITY_COLOR.get(alert.severity, "#CCCCCC")
    return {
        "attachments": [
            {
                "color": color,
                "title": f"{emoji} [{alert.severity.value.upper()}] {alert.name}",
                "text": alert.message,
                "fields": [
                    {"title": "Namespace", "value": alert.namespace or "N/A", "short": True},
                    {"title": "Resource", "value": alert.resource or "N/A", "short": True},
                    {"title": "Time", "value": alert.timestamp.isoformat(), "short": True},
                ],
                "footer": f"InfraOS AI | {extra}" if extra else "InfraOS AI",
            }
        ]
    }


class SlackNotifier:
    """Send alerts and notifications to Slack via incoming webhook."""

    def __init__(self) -> None:
        self._webhook = settings.slack_webhook_url
        self._timeout = 5.0

    @property
    def enabled(self) -> bool:
        return bool(self._webhook and self._webhook.startswith("https://"))

    async def send_alert(self, alert: Alert) -> bool:
        if not self.enabled:
            logger.debug("Slack webhook not configured, skipping notification")
            return False
        payload = _build_payload(alert)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._webhook, json=payload)
                resp.raise_for_status()
                logger.info("Slack notification sent for alert: %s", alert.name)
                return True
        except Exception as exc:
            logger.error("Failed to send Slack notification: %s", exc)
            return False

    async def send_message(self, text: str) -> bool:
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._webhook, json={"text": text})
                resp.raise_for_status()
                return True
        except Exception as exc:
            logger.error("Failed to send Slack message: %s", exc)
            return False
