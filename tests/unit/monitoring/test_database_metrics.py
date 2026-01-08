"""Unit tests for database metrics."""

import pytest
from prometheus_client import CollectorRegistry

from src.monitoring.metrics.database_metrics import DatabaseMetrics


class TestDatabaseMetrics:
    """Test DatabaseMetrics class."""

    @pytest.fixture
    def metrics(self):
        """Create DatabaseMetrics instance with isolated registry."""
        m = DatabaseMetrics()
        m.registry = CollectorRegistry()
        m.register()
        return m

    def test_register_creates_all_metrics(self, metrics):
        """Test that register creates all 4 metrics."""
        assert metrics.connections_active is not None
        assert metrics.query_duration_seconds is not None
        assert metrics.queries_total is not None
        assert metrics.errors_total is not None

    def test_connection_tracking(self, metrics):
        """Test active connection gauge."""
        metrics.connections_active.set(3)
        assert metrics.connections_active._value.get() == 3

        metrics.connections_active.inc()
        assert metrics.connections_active._value.get() == 4

        metrics.connections_active.dec()
        assert metrics.connections_active._value.get() == 3

    def test_connection_reset(self, metrics):
        """Test connection count can be reset."""
        metrics.connections_active.set(10)
        metrics.connections_active.set(0)
        assert metrics.connections_active._value.get() == 0

    def test_query_duration_histogram(self, metrics):
        """Test query duration tracking."""
        metrics.query_duration_seconds.labels(operation="SELECT").observe(0.05)
        metrics.query_duration_seconds.labels(operation="INSERT").observe(0.02)

        assert metrics.query_duration_seconds.labels(operation="SELECT")._sum.get() > 0
        assert metrics.query_duration_seconds.labels(operation="INSERT")._sum.get() > 0

    def test_query_duration_multiple_operations(self, metrics):
        """Test query duration for multiple operation types."""
        operations = ["SELECT", "INSERT", "UPDATE", "DELETE"]
        for op in operations:
            metrics.query_duration_seconds.labels(operation=op).observe(0.01)

        for op in operations:
            assert (
                metrics.query_duration_seconds.labels(operation=op)._sum.get() == 0.01
            )

    def test_query_counter(self, metrics):
        """Test query counter with status labels."""
        metrics.queries_total.labels(operation="SELECT", status="success").inc()
        metrics.queries_total.labels(operation="SELECT", status="error").inc()

        success = metrics.queries_total.labels(
            operation="SELECT", status="success"
        )._value.get()
        error = metrics.queries_total.labels(
            operation="SELECT", status="error"
        )._value.get()

        assert success >= 1
        assert error >= 1

    def test_query_counter_multiple_increments(self, metrics):
        """Test query counter with multiple increments."""
        for _ in range(5):
            metrics.queries_total.labels(operation="SELECT", status="success").inc()

        count = metrics.queries_total.labels(
            operation="SELECT", status="success"
        )._value.get()
        assert count == 5

    def test_error_tracking(self, metrics):
        """Test database error tracking."""
        metrics.errors_total.labels(error_type="connection").inc()
        metrics.errors_total.labels(error_type="timeout").inc()
        metrics.errors_total.labels(error_type="deadlock").inc()

        assert metrics.errors_total.labels(error_type="connection")._value.get() >= 1
        assert metrics.errors_total.labels(error_type="timeout")._value.get() >= 1
        assert metrics.errors_total.labels(error_type="deadlock")._value.get() >= 1

    def test_error_counting_accumulates(self, metrics):
        """Test that error counts accumulate correctly."""
        metrics.errors_total.labels(error_type="connection").inc()
        metrics.errors_total.labels(error_type="connection").inc()
        metrics.errors_total.labels(error_type="connection").inc()

        assert metrics.errors_total.labels(error_type="connection")._value.get() == 3

    def test_histogram_buckets(self, metrics):
        """Test that query duration histogram has proper buckets."""
        # Buckets: [0.001, 0.01, 0.1, 0.5, 1, 2, 5]
        metrics.query_duration_seconds.labels(operation="SELECT").observe(0.005)
        metrics.query_duration_seconds.labels(operation="SELECT").observe(0.5)
        metrics.query_duration_seconds.labels(operation="SELECT").observe(3.0)

        total = metrics.query_duration_seconds.labels(operation="SELECT")._sum.get()
        assert total == pytest.approx(3.505, rel=0.01)
