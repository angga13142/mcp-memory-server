"""Metrics utility functions."""

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .base import metric_registry


def get_metrics() -> bytes:
    """Get latest metrics in Prometheus format."""
    return generate_latest(metric_registry.registry)
