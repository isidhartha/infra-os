"""Structured logging setup for InfraOS AI."""

from __future__ import annotations

import logging
import sys
from typing import Any

from .config import get_settings


def setup_logging() -> logging.Logger:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "httpcore", "httpx", "kubernetes"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return logging.getLogger(settings.app_name)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class LogContext:
    """Context manager for structured log fields."""

    def __init__(self, logger: logging.Logger, **fields: Any) -> None:
        self._logger = logger
        self._fields = fields

    def info(self, msg: str) -> None:
        self._logger.info("%s | %s", msg, self._fields)

    def warning(self, msg: str) -> None:
        self._logger.warning("%s | %s", msg, self._fields)

    def error(self, msg: str) -> None:
        self._logger.error("%s | %s", msg, self._fields)
