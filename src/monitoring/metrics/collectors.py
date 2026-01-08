"""
Module: collectors.py

Description:
    Decorators and helper functions for collecting metrics across the
    application. These helpers wrap operational code to record latency
    and success/failure counters without duplicating instrumentation
    logic.

Usage:
    from src.monitoring.metrics import track_session_operation

    @track_session_operation
    async def run_session():
        ...

Author: GitHub Copilot
Date: 2026-01-08
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any

from src.monitoring.errors import handle_metric_error

from .database_metrics import database_metrics
from .journal_metrics import journal_metrics
from .system_metrics import system_metrics
from .vector_store_metrics import vector_store_metrics

logger = logging.getLogger(__name__)


def track_session_operation(func: Callable[..., Awaitable[dict[str, Any]]]):
    """Decorator to track session operations and outcomes."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
        except Exception:
            journal_metrics.increment_session("failed")
            raise

        status = "success" if result.get("success") else "failed"
        journal_metrics.increment_session(status)
        return result

    return wrapper


def track_reflection_generation(func: Callable[..., Awaitable[dict[str, Any]]]):
    """Decorator to track reflection generation latency and outcome."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
        except Exception:
            journal_metrics.increment_reflection("failed")
            raise

        duration = time.time() - start_time
        journal_metrics.observe_reflection_generation(duration)
        journal_metrics.increment_reflection("success")
        return result

    return wrapper


def track_db_query(operation: str):
    """Decorator factory to track database queries."""

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
            except Exception:
                database_metrics.observe_query(
                    operation, time.time() - start_time, "failed"
                )
                raise

            duration = time.time() - start_time
            database_metrics.observe_query(operation, duration, "success")
            return result

        return wrapper

    return decorator


def track_vector_operation(operation: str):
    """Decorator factory to track vector store operations."""

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
            except Exception:
                if operation == "embed":
                    vector_store_metrics.observe_embedding_time(0, "failed")
                elif operation == "search":
                    vector_store_metrics.observe_search_time(0, "failed")
                raise

            duration = time.time() - start_time
            if operation == "embed":
                vector_store_metrics.observe_embedding_time(duration, "success")
            elif operation == "search":
                vector_store_metrics.observe_search_time(duration, "success")
            return result

        return wrapper

    return decorator


@handle_metric_error(logger)
async def update_system_metrics() -> None:
    """Update system metrics in a safe wrapper."""
    await system_metrics.update()


@handle_metric_error(logger)
async def update_vector_store_metrics(vector_store: Any) -> None:
    """Update vector store size and count gauges."""
    count = await vector_store.count()
    vector_store_metrics.set_memory_count(count)

    persist_dir = Path(getattr(vector_store, "persist_directory", ""))
    if not persist_dir:
        return

    if persist_dir.exists():
        total_size = sum(
            f.stat().st_size for f in persist_dir.rglob("*") if f.is_file()
        )
        vector_store_metrics.set_store_size(total_size)


__all__ = [
    "track_session_operation",
    "track_reflection_generation",
    "track_db_query",
    "track_vector_operation",
    "update_system_metrics",
    "update_vector_store_metrics",
    "MetricCache",
    "OptimizedMetricCollector",
    "BatchMetricCollector",
    "LazyMetricCollector",
]


@dataclass
class MetricCache:
    """Cache container for metric values with TTL support."""

    values: dict[str, Any] = field(default_factory=dict)
    last_updated: datetime | None = None
    ttl_seconds: int = 30

    def is_expired(self) -> bool:
        if self.last_updated is None:
            return True
        age = (datetime.now(UTC) - self.last_updated).total_seconds()
        return age > self.ttl_seconds

    def update(self, values: dict[str, Any]) -> None:
        self.values = values
        self.last_updated = datetime.now(UTC)

    def get(self) -> dict[str, Any]:
        return self.values


class OptimizedMetricCollector:
    """Collect metrics with caching and concurrency control."""

    def __init__(self, ttl_seconds: int = 30) -> None:
        self._cache = MetricCache(ttl_seconds=ttl_seconds)
        self._lock = asyncio.Lock()

    async def collect_with_cache(self) -> dict[str, Any]:
        if not self._cache.is_expired():
            return self._cache.get()

        async with self._lock:
            if not self._cache.is_expired():
                return self._cache.get()
            metrics = await self._collect_metrics()
            self._cache.update(metrics)
            return metrics

    async def _collect_metrics(self) -> dict[str, Any]:
        raise NotImplementedError


class BatchMetricCollector:
    """Collect operations in batches before processing."""

    def __init__(self, batch_size: int = 100) -> None:
        self.batch_size = batch_size
        self._batch: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def add_to_batch(self, operation: dict[str, Any]) -> None:
        async with self._lock:
            self._batch.append(operation)
            if len(self._batch) >= self.batch_size:
                await self._flush_batch()

    async def _flush_batch(self) -> None:
        if not self._batch:
            return
        batch = self._batch.copy()
        self._batch.clear()
        asyncio.create_task(self._process_batch(batch))

    async def _process_batch(self, batch: list[dict[str, Any]]) -> None:
        raise NotImplementedError


class LazyMetricCollector:
    """Collect metrics lazily when marked dirty."""

    def __init__(self) -> None:
        self._metrics: dict[str, Any] | None = None
        self._dirty = True

    def mark_dirty(self) -> None:
        self._dirty = True

    async def get_metrics(self) -> dict[str, Any]:
        if self._dirty:
            self._metrics = await self._collect()
            self._dirty = False
        return self._metrics or {}

    async def _collect(self) -> dict[str, Any]:
        raise NotImplementedError
