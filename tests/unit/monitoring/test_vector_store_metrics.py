"""Unit tests for vector store metrics."""

import pytest
from prometheus_client import CollectorRegistry

from src.monitoring.metrics.vector_store_metrics import VectorStoreMetrics


class TestVectorStoreMetrics:
    """Test VectorStoreMetrics class."""

    @pytest.fixture
    def metrics(self):
        """Create VectorStoreMetrics instance with isolated registry."""
        m = VectorStoreMetrics()
        m.registry = CollectorRegistry()
        m.register()
        return m

    def test_register_creates_all_metrics(self, metrics):
        """Test that register creates all 6 metrics."""
        assert metrics.embeddings_generated_total is not None
        assert metrics.embedding_seconds is not None
        assert metrics.searches_total is not None
        assert metrics.search_results is not None
        assert metrics.memory_count is not None
        assert metrics.errors_total is not None

    def test_embedding_generation(self, metrics):
        """Test embedding generation metrics."""
        metrics.embeddings_generated_total.labels(status="success").inc(5)
        metrics.embedding_seconds.observe(0.1)

        assert (
            metrics.embeddings_generated_total.labels(status="success")._value.get()
            == 5
        )
        assert metrics.embedding_seconds._sum.get() > 0

    def test_embedding_generation_with_errors(self, metrics):
        """Test embedding generation with error tracking."""
        metrics.embeddings_generated_total.labels(status="success").inc(10)
        metrics.embeddings_generated_total.labels(status="error").inc(2)

        success = metrics.embeddings_generated_total.labels(
            status="success"
        )._value.get()
        error = metrics.embeddings_generated_total.labels(status="error")._value.get()

        assert success == 10
        assert error == 2

    def test_embedding_duration_histogram(self, metrics):
        """Test embedding duration histogram."""
        durations = [0.02, 0.05, 0.1, 0.5, 1.0]
        for d in durations:
            metrics.embedding_seconds.observe(d)

        total = metrics.embedding_seconds._sum.get()
        assert total == pytest.approx(sum(durations), rel=0.01)

    def test_search_metrics(self, metrics):
        """Test vector search metrics."""
        metrics.searches_total.labels(status="success").inc()
        metrics.search_results.observe(10)

        assert metrics.searches_total.labels(status="success")._value.get() >= 1
        assert metrics.search_results._sum.get() > 0

    def test_search_results_histogram(self, metrics):
        """Test search results histogram with various counts."""
        # Buckets: [0, 1, 5, 10, 20, 50, 100]
        metrics.search_results.observe(0)  # No results
        metrics.search_results.observe(3)  # Few results
        metrics.search_results.observe(15)  # Medium results
        metrics.search_results.observe(75)  # Many results

        total = metrics.search_results._sum.get()
        assert total == 93

    def test_memory_count_gauge(self, metrics):
        """Test memory count tracking."""
        metrics.memory_count.set(100)
        assert metrics.memory_count._value.get() == 100

        metrics.memory_count.inc(5)
        assert metrics.memory_count._value.get() == 105

        metrics.memory_count.dec(10)
        assert metrics.memory_count._value.get() == 95

    def test_memory_count_reset(self, metrics):
        """Test memory count can be reset."""
        metrics.memory_count.set(1000)
        metrics.memory_count.set(500)
        assert metrics.memory_count._value.get() == 500

    def test_error_tracking(self, metrics):
        """Test vector store error tracking."""
        metrics.errors_total.labels(error_type="embedding").inc()
        metrics.errors_total.labels(error_type="search").inc()
        metrics.errors_total.labels(error_type="storage").inc()

        assert metrics.errors_total.labels(error_type="embedding")._value.get() >= 1
        assert metrics.errors_total.labels(error_type="search")._value.get() >= 1
        assert metrics.errors_total.labels(error_type="storage")._value.get() >= 1

    def test_multiple_operations_tracking(self, metrics):
        """Test tracking multiple operations simultaneously."""
        # Simulate realistic workflow
        metrics.memory_count.set(100)

        # Generate embeddings
        for _ in range(5):
            metrics.embeddings_generated_total.labels(status="success").inc()
            metrics.embedding_seconds.observe(0.1)
            metrics.memory_count.inc()

        # Perform searches
        for _ in range(10):
            metrics.searches_total.labels(status="success").inc()
            metrics.search_results.observe(5)

        assert (
            metrics.embeddings_generated_total.labels(status="success")._value.get()
            == 5
        )
        assert metrics.searches_total.labels(status="success")._value.get() == 10
        assert metrics.memory_count._value.get() == 105
