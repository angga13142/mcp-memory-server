"""Deprecated metrics module.

This module now re-exports the monitoring package to maintain backward
compatibility. Please import from src.monitoring.metrics instead.
"""
from __future__ import annotations

from warnings import warn

from src.monitoring.metrics import *  # noqa: F401,F403

warn(
    "src.utils.metrics is deprecated; use src.monitoring.metrics instead.",
    DeprecationWarning,
    stacklevel=2,
)
