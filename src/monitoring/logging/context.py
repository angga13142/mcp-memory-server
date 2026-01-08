"""Logging context management."""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variables
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_correlation_id() -> str:
    """Get current correlation ID or generate new one."""
    correlation_id = correlation_id_var.get()
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate and set a new correlation ID."""
    new_id = str(uuid.uuid4())
    set_correlation_id(new_id)
    return new_id


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    correlation_id_var.set(None)


# User ID Management
def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return user_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set current user ID."""
    user_id_var.set(user_id)


# Request ID Management
def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set current request ID."""
    request_id_var.set(request_id)


# Alias for compatibility
clear_context = clear_correlation_id


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record):
        """Add correlation ID to record."""
        record.correlation_id = get_correlation_id()
        record.user_id = get_user_id()
        record.request_id = get_request_id()
        return True


class LogContext:
    """Context manager for logging context."""

    def __init__(
        self, correlation_id: Optional[str] = None, user_id: Optional[str] = None
    ):
        """Initialize context."""
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.user_id = user_id
        self._tokens = {}

    def __enter__(self):
        """Enter context."""
        self._tokens["correlation_id"] = correlation_id_var.set(self.correlation_id)
        if self.user_id:
            self._tokens["user_id"] = user_id_var.set(self.user_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if "correlation_id" in self._tokens:
            correlation_id_var.reset(self._tokens["correlation_id"])
        if "user_id" in self._tokens:
            user_id_var.reset(self._tokens["user_id"])
