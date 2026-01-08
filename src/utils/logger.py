"""Structured logging configuration."""

import logging
import sys
from typing import Any


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


class StructuredLogger:
    """Logger with structured context support."""

    def __init__(self, name: str, level: str = "INFO"):
        self._logger = get_logger(name, level)
        self._context: dict[str, Any] = {}

    def with_context(self, **kwargs: Any) -> "StructuredLogger":
        """Add context to log messages."""
        new_logger = StructuredLogger.__new__(StructuredLogger)
        new_logger._logger = self._logger
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _format_message(self, message: str) -> str:
        """Format message with context."""
        if self._context:
            context_str = " ".join(f"{k}={v}" for k, v in self._context.items())
            return f"{message} | {context_str}"
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(self._format_message(message), **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(self._format_message(message), **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(self._format_message(message), **kwargs)
