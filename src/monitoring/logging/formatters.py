"""Structured logging formatters."""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add custom fields from extra
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "correlation_id",
                "user_id",
                "request_id",
            ]:
                try:
                    json.dumps(value)  # Check if JSON serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data)


# Alias
StructuredFormatter = JSONFormatter


class ColoredFormatter(logging.Formatter):
    """Format logs with colors for console output."""

    grey = "\x1b[38;20m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + reset,
        logging.INFO: blue
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + reset,
        logging.WARNING: yellow
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + reset,
        logging.ERROR: red
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + reset,
        logging.CRITICAL: bold_red
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
