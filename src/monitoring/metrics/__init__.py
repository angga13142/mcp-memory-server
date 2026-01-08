"""Metrics module exports."""

from .base import MetricRegistry, metric_registry
from .database_metrics import DatabaseMetrics, database_metrics
from .journal_metrics import JournalMetrics, journal_metrics
from .system_metrics import SystemMetrics, system_metrics  # ADD THIS LINE
from .vector_store_metrics import VectorStoreMetrics, vector_store_metrics

# Register all collectors
metric_registry.register_collector(journal_metrics)
metric_registry.register_collector(database_metrics)
metric_registry.register_collector(vector_store_metrics)
metric_registry.register_collector(system_metrics)  # ADD THIS LINE

__all__ = [
    "MetricRegistry",
    "metric_registry",
    "JournalMetrics",
    "journal_metrics",
    "DatabaseMetrics",
    "database_metrics",
    "VectorStoreMetrics",
    "vector_store_metrics",
    "SystemMetrics",  # ADD THIS
    "system_metrics",  # ADD THIS
]
