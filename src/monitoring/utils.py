"""Utility helpers for monitoring responses and formatting."""

from __future__ import annotations

from typing import Any


def success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    **extra: Any,
) -> dict[str, Any]:
    """Create a standardized success response payload."""
    response: dict[str, Any] = {
        "success": True,
        "message": message,
        "error": None,
    }
    if data is not None:
        response["data"] = data
    response.update(extra)
    return response


def error_response(
    error: str,
    error_type: str | None = None,
    tip: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Create a standardized error response payload."""
    response: dict[str, Any] = {
        "success": False,
        "error": error,
        "message": None,
    }
    if error_type:
        response["error_type"] = error_type
    if tip:
        response["tip"] = tip
    response.update(extra)
    return response


def format_duration(seconds: float) -> str:
    """Format duration in a human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"

    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.0f}m"

    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f"{hours}h {remaining_minutes}m" if remaining_minutes else f"{hours}h"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on error."""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


__all__ = [
    "success_response",
    "error_response",
    "format_duration",
    "safe_divide",
    "truncate_string",
]
