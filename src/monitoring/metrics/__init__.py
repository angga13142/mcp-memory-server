"""
Metrics module exports and registry wiring.

Importing this module initializes and registers all metric collectors so
metrics are ready for use throughout the application.
"""
from .base import MetricRegistry, app_info, get_metrics, metric_registry
from .collectors import (
    BatchMetricCollector,
    LazyMetricCollector,
    MetricCache,
    OptimizedMetricCollector,
    track_db_query,
    track_reflection_generation,
    track_session_operation,
    track_vector_operation,
    update_system_metrics,
    update_vector_store_metrics,
)
from .database_metrics import DatabaseMetrics, database_metrics
from .journal_metrics import JournalMetrics, journal_metrics
from .system_metrics import SystemMetrics, system_metrics
from .vector_store_metrics import VectorStoreMetrics, vector_store_metrics

# Register all collectors once
metric_registry.register_collector(journal_metrics)
metric_registry.register_collector(database_metrics)
metric_registry.register_collector(vector_store_metrics)
metric_registry.register_collector(system_metrics)

__all__ = [
    "MetricRegistry",
    "app_info",
    "get_metrics",
    "metric_registry",
    "JournalMetrics",
    "journal_metrics",
    "DatabaseMetrics",
    "database_metrics",
    "VectorStoreMetrics",
    "vector_store_metrics",
    "SystemMetrics",
    "system_metrics",
    "MetricCache",
    "OptimizedMetricCollector",
    "BatchMetricCollector",
    "LazyMetricCollector",
    "track_session_operation",
    "track_reflection_generation",
    "track_db_query",
    "track_vector_operation",
    "update_system_metrics",
    "update_vector_store_metrics",
]
