"""
Error handling utilities for the monitoring module.
"""
from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable


class MonitoringError(Exception):
    """Base exception for monitoring module."""


class MetricCollectionError(MonitoringError):
    """Error during metric collection."""


class LoggingConfigError(MonitoringError):
    """Error in logging configuration."""


def handle_metric_error(logger: logging.Logger, default_value: Any = None) -> Callable:
    """Decorator to handle metric collection errors gracefully."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                return default_value

        return wrapper

    return decorator


def handle_metric_error_async(logger: logging.Logger, default_value: Any = None) -> Callable:
    """Async version of handle_metric_error."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                return default_value

        return wrapper

    return decorator


__all__ = [
    "MonitoringError",
    "MetricCollectionError",
    "LoggingConfigError",
    "handle_metric_error",
    "handle_metric_error_async",
]
