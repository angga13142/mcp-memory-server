"""
Module: vector_store_metrics.py

Description:
    Prometheus metrics for vector store operations such as embedding
    generation, search latency, and storage footprint.

Usage:
    from src.monitoring.metrics import vector_store_metrics

    vector_store_metrics.observe_embedding_time(0.3, "success")
    vector_store_metrics.observe_search_time(0.05, "success")

Metrics Exposed:
    - mcp_vector_embeddings_generated_total: Counter for embeddings by status
    - mcp_vector_embedding_seconds: Histogram for embedding latency
    - mcp_vector_searches_total: Counter for searches by status
    - mcp_vector_search_seconds: Histogram for search latency
    - mcp_vector_store_size_bytes: Gauge for on-disk size
    - mcp_vector_memory_count: Gauge for number of memories

Author: GitHub Copilot
Date: 2026-01-08
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from .base import MetricCollector


class VectorStoreMetrics(MetricCollector):
    """Metrics for vector store operations."""

    def __init__(self) -> None:
        self.embeddings_generated: Counter | None = None
        self.embedding_time: Histogram | None = None
        self.searches_total: Counter | None = None
        self.search_time: Histogram | None = None
        self.store_size: Gauge | None = None
        self.memory_count: Gauge | None = None

    def register(self) -> None:
        """Register vector store metrics."""
        self.embeddings_generated = Counter(
            "mcp_vector_embeddings_generated_total",
            "Total embeddings generated",
            ["status"],
        )

        self.embedding_time = Histogram(
            "mcp_vector_embedding_seconds",
            "Embedding generation time",
            buckets=[0.1, 0.5, 1, 2, 5, 10],
        )

        self.searches_total = Counter(
            "mcp_vector_searches_total",
            "Total vector searches",
            ["status"],
        )

        self.search_time = Histogram(
            "mcp_vector_search_seconds",
            "Vector search time",
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 2],
        )

        self.store_size = Gauge(
            "mcp_vector_store_size_bytes",
            "Vector store size in bytes",
        )

        self.memory_count = Gauge(
            "mcp_vector_memory_count",
            "Number of memories in store",
        )

    def collect(self) -> dict[str, float]:
        """Collect vector store gauges."""
        return {
            "store_size": self._require(self.store_size, "store_size")._value.get(),
            "memory_count": self._require(
                self.memory_count, "memory_count"
            )._value.get(),
        }

    def observe_embedding_time(self, seconds: float, status: str) -> None:
        """Record embedding generation duration."""
        if seconds < 0:
            raise ValueError("Duration cannot be negative")
        self._require(self.embedding_time, "embedding_time").observe(seconds)
        self._require(self.embeddings_generated, "embeddings_generated").labels(
            status=status
        ).inc()

    def observe_search_time(self, seconds: float, status: str) -> None:
        """Record vector search duration."""
        if seconds < 0:
            raise ValueError("Duration cannot be negative")
        self._require(self.search_time, "search_time").observe(seconds)
        self._require(self.searches_total, "searches_total").labels(status=status).inc()

    def set_store_size(self, bytes_size: int) -> None:
        """Set on-disk size of the vector store."""
        if bytes_size < 0:
            raise ValueError("Store size cannot be negative")
        self._require(self.store_size, "store_size").set(bytes_size)

    def set_memory_count(self, count: int) -> None:
        """Set number of memories in the store."""
        if count < 0:
            raise ValueError("Memory count cannot be negative")
        self._require(self.memory_count, "memory_count").set(count)

    def _require(self, metric, name: str):
        """Ensure metric is registered before use."""
        if metric is None:
            raise RuntimeError(f"Metric '{name}' accessed before registration")
        return metric


# Singleton instance
vector_store_metrics = VectorStoreMetrics()

__all__ = ["VectorStoreMetrics", "vector_store_metrics"]
