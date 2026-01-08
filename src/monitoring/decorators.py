"""Decorators for metrics tracking."""

import asyncio
import functools
import time
from typing import Any, Callable

from prometheus_client import Counter, Histogram


def track_time(histogram: Histogram, labels: dict = None):
    """
    Decorator to track execution time.

    Args:
        histogram: Prometheus Histogram to record duration
        labels: Optional labels for the metric
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def count_calls(counter: Counter, labels: dict = None):
    """
    Decorator to count function calls.

    Args:
        counter:  Prometheus Counter to increment
        labels: Optional labels for the metric
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                if labels:
                    counter.labels(**labels, status="success").inc()
                else:
                    counter.labels(status="success").inc()
                return result
            except Exception as e:
                if labels:
                    counter.labels(**labels, status="error").inc()
                else:
                    counter.labels(status="error").inc()
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                if labels:
                    counter.labels(**labels, status="success").inc()
                else:
                    counter.labels(status="success").inc()
                return result
            except Exception as e:
                if labels:
                    counter.labels(**labels, status="error").inc()
                else:
                    counter.labels(status="error").inc()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
