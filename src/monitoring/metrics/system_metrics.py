"""
Module: system_metrics.py

Description:
    Prometheus metrics for host system resources such as CPU and memory
    usage. Designed to be updated periodically by background tasks.

Usage:
    from src.monitoring.metrics import system_metrics

    await system_metrics.update()

Metrics Exposed:
    - mcp_system_memory_usage_bytes: Gauge for memory usage
    - mcp_system_cpu_usage_percent: Gauge for CPU utilization

Author: GitHub Copilot
Date: 2026-01-08
"""
from __future__ import annotations

from typing import Dict

from prometheus_client import Gauge

from .base import MetricCollector


class SystemMetrics(MetricCollector):
    """Metrics describing system resource utilization."""

    def __init__(self) -> None:
        self.memory_usage: Gauge | None = None
        self.cpu_usage: Gauge | None = None

    def register(self) -> None:
        """Register system metrics."""
        self.memory_usage = Gauge(
            "mcp_system_memory_usage_bytes",
            "Memory usage in bytes",
        )

        self.cpu_usage = Gauge(
            "mcp_system_cpu_usage_percent",
            "CPU usage percentage",
        )

    def collect(self) -> Dict[str, float]:
        """Collect system metrics."""
        return {
            "memory_usage": self._require(self.memory_usage, "memory_usage")._value.get(),
            "cpu_usage": self._require(self.cpu_usage, "cpu_usage")._value.get(),
        }

    async def update(self) -> None:
        """Update CPU and memory gauges using psutil if available."""
        try:
            import psutil
        except ImportError:
            return

        memory = psutil.virtual_memory()
        self._require(self.memory_usage, "memory_usage").set(memory.used)
        cpu_percent = psutil.cpu_percent(interval=1)
        self._require(self.cpu_usage, "cpu_usage").set(cpu_percent)

    def _require(self, metric, name: str):
        """Ensure metric is registered before use."""
        if metric is None:
            raise RuntimeError(f"Metric '{name}' accessed before registration")
        return metric


system_metrics = SystemMetrics()

__all__ = ["SystemMetrics", "system_metrics"]
