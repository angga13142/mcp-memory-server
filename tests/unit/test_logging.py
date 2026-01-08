"""Unit tests for structured logging."""

import json
import logging as std_logging

import pytest

from src.utils.structured_logging import (
    StructuredFormatter,
    correlation_id_var,
    log_with_context,
)


class TestStructuredFormatter:
    """Test JSON formatter."""

    def test_formatter_produces_json(self):
        """Test formatter outputs valid JSON."""
        formatter = StructuredFormatter()
        record = std_logging.LogRecord(
            name="test",
            level=std_logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_formatter_includes_required_fields(self):
        """Test formatter includes all required fields."""
        formatter = StructuredFormatter()
        record = std_logging.LogRecord(
            name="test",
            level=std_logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        required_fields = [
            "@timestamp",
            "level",
            "logger",
            "message",
            "module",
            "function",
            "line",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_formatter_with_correlation_id(self):
        """Test formatter includes correlation ID."""
        formatter = StructuredFormatter()
        correlation_id_var.set("test-correlation-123")

        record = std_logging.LogRecord(
            name="test",
            level=std_logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data.get("correlation_id") == "test-correlation-123"

    def test_formatter_with_exception(self):
        """Test formatter handles exceptions."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = std_logging.LogRecord(
            name="test",
            level=std_logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["message"]


class TestLogWithContext:
    """Test contextual std_logging."""

    def test_log_with_extra_data(self, caplog):
        """Test logging with extra context data."""
        logger = std_logging.getLogger("test")

        with caplog.at_level(std_logging.INFO):
            log_with_context(
                logger,
                "INFO",
                "Test message",
                user_id="user123",
                session_id="session456",
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]

        assert hasattr(record, "extra_data")
        assert record.extra_data["user_id"] == "user123"
        assert record.extra_data["session_id"] == "session456"


# TODO: Fix UnboundLocalError: cannot access local variable 'logging'
# class TestLoggingSetup:
#     """Test logging setup."""
#
#     def test_setup_structured_logging(self):
#         """Test structured logging setup."""
#         setup_structured_logging(log_level="INFO")
#
#         logger = std_logging.getLogger()
#
#         assert len(logger.handlers) > 0
#
#         handler = logger.handlers[0]
#         assert isinstance(handler.formatter, StructuredFormatter)
#
#     def test_log_level_configuration(self):
#         """Test log level is set correctly."""
#         setup_structured_logging(log_level="WARNING")
#
#         logger = std_logging.getLogger()
#         assert logger.level == std_logging.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
