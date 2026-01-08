"""Structured logging with JSON output."""

import json
import logging
import logging.handlers
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "@timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        if record.stack_info:
            log_data["stack_info"] = record.stack_info

        return json.dumps(log_data, default=str)


def setup_structured_logging(log_level: str = "INFO", log_file: str | None = None):
    """Setup structured JSON logging."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers.clear()

    formatter = StructuredFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        from pathlib import Path

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=50 * 1024 * 1024, backupCount=7
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def log_with_context(
    logger: logging.Logger, level: str, message: str, **extra_data: Any
):
    """Log with additional context data."""
    log_func = getattr(logger, level.lower())
    log_func(message, extra={"extra_data": extra_data})


def log_session_start(session_id: str, task: str):
    """Log session start event."""
    logger = logging.getLogger(__name__)
    log_with_context(
        logger,
        "INFO",
        "Work session started",
        event="session_start",
        session_id=session_id,
        task=task,
    )


def log_session_end(session_id: str, duration_minutes: int, status: str):
    """Log session end event."""
    logger = logging.getLogger(__name__)
    log_with_context(
        logger,
        "INFO",
        "Work session ended",
        event="session_end",
        session_id=session_id,
        duration_minutes=duration_minutes,
        status=status,
    )


def log_reflection_generated(session_id: str, generation_time: float):
    """Log reflection generation event."""
    logger = logging.getLogger(__name__)
    log_with_context(
        logger,
        "INFO",
        "Reflection generated",
        event="reflection_generated",
        session_id=session_id,
        generation_time_seconds=generation_time,
    )
