"""Base classes for metrics collection."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary


class MetricCollector(ABC):
    """Base class for metric collectors."""

    def __init__(self):
        """Initialize the collector."""
        self.registry = None

    @abstractmethod
    def register(self) -> None:
        """Register metrics with Prometheus."""
        pass

    def collect(self) -> Dict[str, Any]:
        """
        Collect current metrics.

        Returns:
            Dictionary of collected metrics
        """
        return {}


class MetricRegistry:
    """Registry for all metric collectors."""

    def __init__(self):
        """Initialize the registry."""
        self._collectors: List[MetricCollector] = []
        self.registry = CollectorRegistry()

    def register_collector(self, collector: MetricCollector) -> None:
        """Register a metric collector."""
        collector.registry = self.registry
        collector.register()
        self._collectors.append(collector)

    def collect_all(self) -> Dict[str, Any]:
        """Collect metrics from all registered collectors."""
        all_metrics = {}
        for collector in self._collectors:
            all_metrics.update(collector.collect())
        return all_metrics


# Global registry instance
metric_registry = MetricRegistry()
