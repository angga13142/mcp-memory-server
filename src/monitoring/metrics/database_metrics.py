"""
Module: database_metrics.py

Description:
    Prometheus metrics for database connectivity and query performance.

Usage:
    from src.monitoring.metrics import database_metrics

    database_metrics.observe_query("select", 0.015, "success")
    current = database_metrics.collect()["connections_active"]

Metrics Exposed:
    - mcp_db_connections_active: Gauge for active database connections
    - mcp_db_connections_total: Counter for total connections by status
    - mcp_db_query_duration_seconds: Histogram of query durations by operation
    - mcp_db_queries_total: Counter for queries by operation and status

Author: GitHub Copilot
Date: 2026-01-08
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from .base import MetricCollector


class DatabaseMetrics(MetricCollector):
    """Metrics for database operations."""

    def __init__(self) -> None:
        self.connections_active: Gauge | None = None
        self.connections_total: Counter | None = None
        self.query_duration: Histogram | None = None
        self.queries_total: Counter | None = None

    def register(self) -> None:
        """Register database metrics."""
        self.connections_active = Gauge(
            "mcp_db_connections_active",
            "Active database connections",
        )

        self.connections_total = Counter(
            "mcp_db_connections_total",
            "Total database connections",
            ["status"],
        )

        self.query_duration = Histogram(
            "mcp_db_query_duration_seconds",
            "Database query duration",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
        )

        self.queries_total = Counter(
            "mcp_db_queries_total",
            "Total database queries",
            ["operation", "status"],
        )

    def collect(self) -> dict[str, float]:
        """Collect database metrics."""
        return {
            "connections_active": self._require(
                self.connections_active, "connections_active"
            )._value.get(),
        }

    def set_active_connections(self, value: int) -> None:
        """Set current active connections."""
        if value < 0:
            raise ValueError("Connections cannot be negative")
        self._require(self.connections_active, "connections_active").set(value)

    def increment_connection(self, status: str) -> None:
        """Increment total connections by status."""
        self._require(self.connections_total, "connections_total").labels(
            status=status
        ).inc()

    def observe_query(self, operation: str, duration: float, status: str) -> None:
        """Record query duration and status."""
        if duration < 0:
            raise ValueError("Duration cannot be negative")
        self._require(self.query_duration, "query_duration").labels(
            operation=operation
        ).observe(duration)
        self._require(self.queries_total, "queries_total").labels(
            operation=operation, status=status
        ).inc()

    def _require(self, metric, name: str):
        """Ensure metric is registered before use."""
        if metric is None:
            raise RuntimeError(f"Metric '{name}' accessed before registration")
        return metric


# Singleton instance
postgres_metrics = DatabaseMetrics()
database_metrics = postgres_metrics

__all__ = ["DatabaseMetrics", "database_metrics", "postgres_metrics"]
