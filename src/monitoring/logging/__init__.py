"""Logging utilities for structured logging and context propagation."""
from .context import (
    LogContext,
    clear_context,
    generate_correlation_id,
    get_correlation_id,
    get_request_id,
    get_user_id,
    set_correlation_id,
    set_request_id,
    set_user_id,
)
from .formatters import ColoredFormatter, StructuredFormatter
from .optimized_formatters import BufferedJsonHandler, LazyJsonFormatter
from .helpers import log_error, log_event, log_reflection_event, log_session_event

__all__ = [
    "StructuredFormatter",
    "ColoredFormatter",
    "LazyJsonFormatter",
    "BufferedJsonHandler",
    "set_correlation_id",
    "get_correlation_id",
    "generate_correlation_id",
    "set_user_id",
    "get_user_id",
    "set_request_id",
    "get_request_id",
    "LogContext",
    "clear_context",
    "log_event",
    "log_session_event",
    "log_reflection_event",
    "log_error",
]
