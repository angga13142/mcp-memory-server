"""
Module: base.py

Description:
    Base metric abstractions and registry helpers for Prometheus metrics
    used by the monitoring package. Centralizes metric registration to
    avoid duplicate collectors and provides a helper to export metrics in
    Prometheus text format.

Usage:
    from src.monitoring.metrics import metric_registry, get_metrics

    metrics_bytes = get_metrics()
    registry_state = metric_registry.collect_all()

Author: GitHub Copilot
Date: 2026-01-08
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from prometheus_client import Info, REGISTRY, generate_latest


class MetricCollector(ABC):
    """Base class for metric collectors."""

    @abstractmethod
    def register(self) -> None:
        """Register Prometheus metrics for this collector."""

    @abstractmethod
    def collect(self) -> Dict[str, float]:
        """Collect metric values for observability endpoints."""


class MetricRegistry:
    """Central registry for all metric collectors."""

    def __init__(self) -> None:
        self._collectors: List[MetricCollector] = []
        self._metrics: Dict[str, Any] = {}

    def register_collector(self, collector: MetricCollector) -> None:
        """Register and initialize a metric collector once."""
        if collector in self._collectors:
            return
        self._collectors.append(collector)
        collector.register()

    def collect_all(self) -> Dict[str, Dict[str, float]]:
        """Collect metrics from all registered collectors."""
        snapshot: Dict[str, Dict[str, float]] = {}
        for collector in self._collectors:
            snapshot[collector.__class__.__name__] = collector.collect()
        return snapshot

    @property
    def metrics(self) -> Dict[str, Any]:
        """Access raw metric objects keyed by name."""
        return self._metrics


def get_metrics() -> bytes:
    """Return metrics in Prometheus text format."""
    return generate_latest(REGISTRY)


# Application metadata exposed as Prometheus Info
app_info = Info("mcp_memory_server", "Application information")
app_info.info({
    "version": "1.0.0",
    "feature": "daily_journal",
    "python_version": "3.11",
})


# Global registry instance
metric_registry = MetricRegistry()

__all__ = [
    "MetricCollector",
    "MetricRegistry",
    "metric_registry",
    "get_metrics",
    "app_info",
]
