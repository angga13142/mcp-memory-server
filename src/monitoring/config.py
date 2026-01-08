"""Monitoring configuration dataclasses and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class MetricsConfig:
    enabled: bool = True
    port: int = 8080
    path: str = "/metrics"
    cache_ttl: int = 30
    batch_size: int = 100
    collection_interval: int = 15


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"
    file: Path | None = None
    max_file_size: int = 50 * 1024 * 1024
    backup_count: int = 7
    structured: bool = True
    sanitize: bool = True
    buffer_size: int = 100


@dataclass
class AlertConfig:
    enabled: bool = True
    prometheus_url: str = "http://localhost:9090"
    alertmanager_url: str = "http://localhost:9093"
    evaluation_interval: int = 30


@dataclass
class SecurityConfig:
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 100
    sanitize_logs: bool = True
    allowed_ips: list[str] = field(default_factory=list)


@dataclass
class MonitoringConfig:
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    @classmethod
    def from_env(cls) -> MonitoringConfig:
        import os

        return cls(
            metrics=MetricsConfig(
                enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
                port=int(os.getenv("METRICS_PORT", "8080")),
                cache_ttl=int(os.getenv("METRICS_CACHE_TTL", "30")),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=os.getenv("LOG_FORMAT", "json"),
                file=Path(os.getenv("LOG_FILE")) if os.getenv("LOG_FILE") else None,
            ),
            security=SecurityConfig(
                rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower()
                == "true",
                max_requests_per_minute=int(os.getenv("RATE_LIMIT_MAX", "100")),
            ),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> MonitoringConfig:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(
            metrics=MetricsConfig(**data.get("metrics", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            alerts=AlertConfig(**data.get("alerts", {})),
            security=SecurityConfig(**data.get("security", {})),
        )


def get_monitoring_config() -> MonitoringConfig:
    """Return cached global monitoring config (env-backed)."""
    return _config or MonitoringConfig.from_env()


def set_monitoring_config(config: MonitoringConfig) -> None:
    """Set the global monitoring configuration instance."""
    global _config
    _config = config


_config: MonitoringConfig | None = None

__all__ = [
    "MetricsConfig",
    "LoggingConfig",
    "AlertConfig",
    "SecurityConfig",
    "MonitoringConfig",
    "get_monitoring_config",
    "set_monitoring_config",
]
