"""Database-specific metrics."""

from prometheus_client import Counter, Gauge, Histogram

from .base import MetricCollector


class DatabaseMetrics(MetricCollector):
    """Metrics for database operations."""

    def __init__(self):
        """Initialize database metrics."""
        super().__init__()
        self.connections_active = None
        self.query_duration_seconds = None
        self.queries_total = None
        self.errors_total = None

    def register(self) -> None:
        """Register database metrics."""
        self.connections_active = Gauge(
            "mcp_db_connections_active",
            "Number of active database connections",
            registry=self.registry,
        )

        self.query_duration_seconds = Histogram(
            "mcp_db_query_duration_seconds",
            "Database query duration",
            ["operation"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5],
            registry=self.registry,
        )

        self.queries_total = Counter(
            "mcp_db_queries_total",
            "Total database queries",
            ["operation", "status"],
            registry=self.registry,
        )

        self.errors_total = Counter(
            "mcp_db_errors_total",
            "Total database errors",
            ["error_type"],
            registry=self.registry,
        )


# Global instance
database_metrics = DatabaseMetrics()
