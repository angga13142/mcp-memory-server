"""
Module: helpers.py

Description:
    Helper functions to standardize structured logging across the
    application.

Author: GitHub Copilot
Date: 2026-01-08
"""

from __future__ import annotations

import logging
from typing import Any


def log_event(
    logger: logging.Logger,
    level: str,
    event: str,
    message: str,
    **extra: Any,
) -> None:
    """Log an event with structured data."""
    extra_data = {
        "event": event,
        **extra,
    }

    log_func = getattr(logger, level.lower())
    log_func(message, extra={"extra_data": extra_data})


def log_session_event(event_type: str, session_id: str, **extra: Any) -> None:
    """Log a session-related event."""
    logger = logging.getLogger("journal.session")

    log_event(
        logger,
        "INFO",
        f"session_{event_type}",
        f"Session {event_type}: {session_id}",
        session_id=session_id,
        **extra,
    )


def log_reflection_event(
    session_id: str, generation_time: float, status: str, **extra: Any
) -> None:
    """Log a reflection generation event."""
    logger = logging.getLogger("journal.reflection")

    log_event(
        logger,
        "INFO",
        "reflection_generated",
        f"Reflection generated for session {session_id}",
        session_id=session_id,
        generation_time_seconds=generation_time,
        status=status,
        **extra,
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: dict[str, Any],
    message: str = "An error occurred",
) -> None:
    """Log an error with full context."""
    logger.error(
        message,
        exc_info=True,
        extra={
            "extra_data": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                **context,
            }
        },
    )


__all__ = [
    "log_event",
    "log_session_event",
    "log_reflection_event",
    "log_error",
]
