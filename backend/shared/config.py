"""Centralized configuration for InfraOS AI."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_model: str = "gpt-4o-mini"

    # Kubernetes
    kubeconfig_path: str = "~/.kube/config"
    k8s_mock_mode: bool = True
    k8s_in_cluster: bool = False

    # Observability
    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3001"
    grafana_api_key: str = ""

    # Storage
    database_url: str = "postgresql://infraos:password@localhost:5432/infraos"
    redis_url: str = "redis://localhost:6379"

    # Notifications
    slack_webhook_url: str = ""

    # App
    log_level: str = "INFO"
    app_name: str = "InfraOS AI"
    version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:3005", "http://localhost:5173"]

    # Alerting thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 90.0
    memory_warning_threshold: float = 75.0
    memory_critical_threshold: float = 90.0
    pod_restart_warning_threshold: int = 5
    pod_restart_critical_threshold: int = 20


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
