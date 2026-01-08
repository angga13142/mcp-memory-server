"""
Module: formatters.py

Description:
    Logging formatters for structured JSON output and colored console
    output.

Usage:
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)

Author: GitHub Copilot
Date: 2026-01-08
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from .context import get_correlation_id, get_user_id


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, include_extra: bool = True) -> None:
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = self._build_base_log(record)

        if self.include_extra:
            log_data.update(self._extract_extra_fields(record))

        if record.exc_info:
            log_data["exception"] = self._format_exception(record)

        return json.dumps(log_data, default=str)

    def _build_base_log(self, record: logging.LogRecord) -> Dict[str, Any]:
        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        extra: Dict[str, Any] = {}

        correlation_id = get_correlation_id()
        if correlation_id:
            extra["correlation_id"] = correlation_id

        user_id = get_user_id()
        if user_id:
            extra["user_id"] = user_id

        if hasattr(record, "extra_data"):
            extra.update(record.extra_data)

        return extra

    def _format_exception(self, record: logging.LogRecord) -> Dict[str, Any]:
        # Extract exception type, message, and stack trace so downstream
        # log processors can index these fields individually.
        return {
            "type": record.exc_info[0].__name__,
            "message": str(record.exc_info[1]),
            "traceback": self.formatException(record.exc_info),
        }


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        formatted = super().format(record)
        return f"{color}{formatted}{self.RESET}"


__all__ = ["StructuredFormatter", "ColoredFormatter"]
