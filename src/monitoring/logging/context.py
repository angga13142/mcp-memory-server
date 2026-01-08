"""
Module: context.py

Description:
    Context variable helpers for propagating correlation, user, and
    request identifiers through log records.

Usage:
    with LogContext(user_id="alice"):
        logger.info("processing request")

Author: GitHub Copilot
Date: 2026-01-08
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional
from uuid import uuid4


_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_correlation_id(correlation_id: str) -> None:
    _correlation_id.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    return _correlation_id.get()


def generate_correlation_id() -> str:
    return str(uuid4())


def set_user_id(user_id: str) -> None:
    _user_id.set(user_id)


def get_user_id() -> Optional[str]:
    return _user_id.get()


def set_request_id(request_id: str) -> None:
    _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def clear_context() -> None:
    _correlation_id.set(None)
    _user_id.set(None)
    _request_id.set(None)


class LogContext:
    """Context manager for logging context propagation."""

    def __init__(
        self,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        self.correlation_id = correlation_id or generate_correlation_id()
        self.user_id = user_id
        self.request_id = request_id

        self._prev_correlation_id: Optional[str] = None
        self._prev_user_id: Optional[str] = None
        self._prev_request_id: Optional[str] = None

    def __enter__(self):
        self._prev_correlation_id = get_correlation_id()
        self._prev_user_id = get_user_id()
        self._prev_request_id = get_request_id()

        set_correlation_id(self.correlation_id)
        if self.user_id:
            set_user_id(self.user_id)
        if self.request_id:
            set_request_id(self.request_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._prev_correlation_id:
            set_correlation_id(self._prev_correlation_id)
        else:
            _correlation_id.set(None)

        if self._prev_user_id:
            set_user_id(self._prev_user_id)
        else:
            _user_id.set(None)

        if self._prev_request_id:
            set_request_id(self._prev_request_id)
        else:
            _request_id.set(None)


__all__ = [
    "set_correlation_id",
    "get_correlation_id",
    "generate_correlation_id",
    "set_user_id",
    "get_user_id",
    "set_request_id",
    "get_request_id",
    "LogContext",
    "clear_context",
]
