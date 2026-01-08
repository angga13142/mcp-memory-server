"""Optimized logging helpers for buffered and lazy JSON formatting."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List


class LazyJsonFormatter(logging.Formatter):
    """JSON formatter that avoids work for filtered-out records."""

    def format(self, record: logging.LogRecord) -> str:
        if not self._should_format(record):
            return ""
        return self._format_json(record)

    def _should_format(self, record: logging.LogRecord) -> bool:
        logger = logging.getLogger(record.name)
        return record.levelno >= logger.level

    def _format_json(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "@timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_data, default=str)


class BufferedJsonHandler(logging.Handler):
    """Handler that buffers log records and flushes in batches."""

    def __init__(self, base_handler: logging.Handler, buffer_size: int = 100) -> None:
        super().__init__()
        self.base_handler = base_handler
        self.buffer_size = buffer_size
        self._buffer: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self._buffer.append(record)
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        for record in self._buffer:
            self.base_handler.emit(record)
        self._buffer.clear()
        self.base_handler.flush()


__all__ = ["LazyJsonFormatter", "BufferedJsonHandler"]
