"""Common decorators for monitoring instrumentation and resilience."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from prometheus_client import Counter, Histogram


def track_operation(
    counter: Counter,
    histogram: Histogram | None = None,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Track operation outcome and latency using Prometheus metrics."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = "failed"
            try:
                result = await func(*args, **kwargs)
                status = "success" if _is_success(result) else "failed"
                return result
            except Exception:
                if logger:
                    logger.exception("Error in %s", func.__name__)
                raise
            finally:
                counter.labels(status=status).inc()
                if histogram:
                    histogram.observe(time.time() - start_time)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = "failed"
            try:
                result = func(*args, **kwargs)
                status = "success" if _is_success(result) else "failed"
                return result
            except Exception:
                if logger:
                    logger.exception("Error in %s", func.__name__)
                raise
            finally:
                counter.labels(status=status).inc()
                if histogram:
                    histogram.observe(time.time() - start_time)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def track_with_context(
    metric_name: str,
    operation_type: str,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Wrap an async operation with log context and structured event logging."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from src.monitoring.logging import LogContext, log_event

            with LogContext():
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    if logger:
                        log_event(
                            logger,
                            "INFO",
                            operation_type,
                            f"{operation_type} completed",
                            duration_seconds=duration,
                            metric=metric_name,
                            status="success",
                        )
                    return result
                except Exception as exc:  # noqa: BLE001
                    duration = time.time() - start_time
                    if logger:
                        log_event(
                            logger,
                            "ERROR",
                            operation_type,
                            f"{operation_type} failed",
                            duration_seconds=duration,
                            metric=metric_name,
                            status="failed",
                            error=str(exc),
                        )
                    raise

        return wrapper

    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Async retry decorator with exponential backoff."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exception = exc
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                "Attempt %s/%s failed for %s: %s. Retrying in %.1fs...",
                                attempt + 1,
                                max_retries,
                                func.__name__,
                                exc,
                                current_delay,
                            )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if logger:
                            logger.error(
                                "All %s retries failed for %s",
                                max_retries,
                                func.__name__,
                            )
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def _is_success(result: Any) -> bool:
    """Determine success status from a result object."""
    return isinstance(result, dict) and bool(result.get("success"))


__all__ = [
    "track_operation",
    "track_with_context",
    "retry_on_error",
]
