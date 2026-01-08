"""Vector store metrics."""

from prometheus_client import Counter, Gauge, Histogram

from .base import MetricCollector


class VectorStoreMetrics(MetricCollector):
    """Metrics for vector store operations."""

    def __init__(self):
        """Initialize vector store metrics."""
        super().__init__()
        self.embeddings_generated_total = None
        self.embedding_seconds = None
        self.searches_total = None
        self.search_results = None
        self.memory_count = None
        self.errors_total = None

    def register(self) -> None:
        """Register vector store metrics."""
        self.embeddings_generated_total = Counter(
            "mcp_vector_embeddings_generated_total",
            "Total embeddings generated",
            ["status"],
            registry=self.registry,
        )

        self.embedding_seconds = Histogram(
            "mcp_vector_embedding_seconds",
            "Time to generate embeddings",
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
            registry=self.registry,
        )

        self.searches_total = Counter(
            "mcp_vector_searches_total",
            "Total vector searches",
            ["status"],
            registry=self.registry,
        )

        self.search_results = Histogram(
            "mcp_vector_search_results",
            "Number of search results returned",
            buckets=[0, 1, 5, 10, 20, 50, 100],
            registry=self.registry,
        )

        self.memory_count = Gauge(
            "mcp_vector_memory_count",
            "Total memories in vector store",
            registry=self.registry,
        )

        self.errors_total = Counter(
            "mcp_vector_errors_total",
            "Total vector store errors",
            ["error_type"],
            registry=self.registry,
        )


# Global instance
vector_store_metrics = VectorStoreMetrics()
