"""Data sanitization helpers for logs and metrics."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Pattern


class DataSanitizer:
    """Sanitize sensitive data from text structures."""

    SENSITIVE_PATTERNS: List[Pattern[str]] = [
        re.compile(r"password[\"\s:=]+[\"']?([^\"'\s]+)", re.IGNORECASE),
        re.compile(r"api[_-]?key[\"\s:=]+[\"']?([^\"'\s]+)", re.IGNORECASE),
        re.compile(r"secret[\"\s:=]+[\"']?([^\"'\s]+)", re.IGNORECASE),
        re.compile(r"token[\"\s:=]+[\"']?([^\"'\s]+)", re.IGNORECASE),
        re.compile(r"bearer\s+([^\s]+)", re.IGNORECASE),
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        re.compile(r"\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"),
    ]

    REDACTION_TEXT = "***REDACTED***"

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        result = text
        for pattern in cls.SENSITIVE_PATTERNS:
            result = pattern.sub(cls.REDACTION_TEXT, result)
        return result

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            if cls._is_sensitive_key(key):
                sanitized[key] = cls.REDACTION_TEXT
            elif isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_dict(item) if isinstance(item, dict)
                    else cls.sanitize_string(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    @classmethod
    def _is_sensitive_key(cls, key: str) -> bool:
        sensitive_keywords = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "key",
            "api_key",
            "apikey",
            "auth",
            "credential",
            "private",
            "ssn",
            "credit_card",
        ]
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in sensitive_keywords)


class SanitizingFormatter(logging.Formatter):
    """Formatter that sanitizes messages and args before formatting."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.sanitizer = DataSanitizer()

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        if isinstance(record.msg, str):
            record.msg = self.sanitizer.sanitize_string(record.msg)

        if record.args:
            record.args = tuple(
                self.sanitizer.sanitize_string(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )

        formatted = super().format(record)
        record.msg = original_msg
        return formatted


__all__ = ["DataSanitizer", "SanitizingFormatter"]
