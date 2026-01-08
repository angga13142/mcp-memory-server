"""
Module: journal_metrics.py

Description:
    Prometheus metrics for journal operations including session tracking,
    reflection generation, and learning capture.

Usage:
    from src.monitoring.metrics import journal_metrics

    journal_metrics.increment_session("success")
    journal_metrics.observe_session_duration(45)

Metrics Exposed:
    - mcp_journal_sessions_total: Counter for total sessions
    - mcp_journal_sessions_active: Gauge for active sessions
    - mcp_journal_session_duration_minutes: Histogram of durations
    - mcp_journal_reflections_generated_total: Counter for reflections
    - mcp_journal_reflection_generation_seconds: Histogram for generation latency
    - mcp_journal_daily_summaries_total: Counter for daily summaries
    - mcp_journal_daily_summary_seconds: Histogram for summary latency
    - mcp_journal_learnings_captured_total: Counter for learnings
    - mcp_journal_challenges_noted_total: Counter for challenges
    - mcp_journal_wins_captured_total: Counter for wins

Author: GitHub Copilot
Date: 2026-01-08
"""
from __future__ import annotations

from typing import Dict

from prometheus_client import Counter, Gauge, Histogram

from .base import MetricCollector


class JournalMetrics(MetricCollector):
    """Metrics for journal operations."""

    def __init__(self) -> None:
        self.sessions_total: Counter | None = None
        self.sessions_active: Gauge | None = None
        self.session_duration: Histogram | None = None
        self.reflections_generated: Counter | None = None
        self.reflection_generation_time: Histogram | None = None
        self.daily_summaries: Counter | None = None
        self.daily_summary_time: Histogram | None = None
        self.learnings_captured: Counter | None = None
        self.challenges_noted: Counter | None = None
        self.wins_captured: Counter | None = None

    def register(self) -> None:
        """Register journal metrics."""
        self.sessions_total = Counter(
            "mcp_journal_sessions_total",
            "Total number of work sessions",
            ["status"],
        )

        self.sessions_active = Gauge(
            "mcp_journal_sessions_active",
            "Number of currently active sessions",
        )

        self.session_duration = Histogram(
            "mcp_journal_session_duration_minutes",
            "Work session duration in minutes",
            buckets=[5, 15, 30, 60, 120, 240, 480],
        )

        self.reflections_generated = Counter(
            "mcp_journal_reflections_generated_total",
            "Total reflections generated",
            ["status"],
        )

        self.reflection_generation_time = Histogram(
            "mcp_journal_reflection_generation_seconds",
            "Time to generate a reflection",
            buckets=[0.5, 1, 2, 5, 10, 30],
        )

        self.daily_summaries = Counter(
            "mcp_journal_daily_summaries_total",
            "Daily summaries generated",
            ["status"],
        )

        self.daily_summary_time = Histogram(
            "mcp_journal_daily_summary_seconds",
            "Daily summary generation time",
            buckets=[1, 2, 5, 10, 30],
        )

        self.learnings_captured = Counter(
            "mcp_journal_learnings_captured_total",
            "Total learnings captured",
        )

        self.challenges_noted = Counter(
            "mcp_journal_challenges_noted_total",
            "Total challenges noted",
        )

        self.wins_captured = Counter(
            "mcp_journal_wins_captured_total",
            "Total wins captured",
        )

    def collect(self) -> Dict[str, float]:
        """Collect current journal metrics for quick inspection."""
        return {
            "sessions_active": self._value(self.sessions_active),
            "sessions_total_success": self._value(self.sessions_total, status="success"),
            "sessions_total_failed": self._value(self.sessions_total, status="failed"),
        }

    def increment_session(self, status: str) -> None:
        """Increment session counter by status."""
        self._require(self.sessions_total, "sessions_total").labels(status=status).inc()

    def set_active_sessions(self, count: int) -> None:
        """Set active sessions gauge."""
        if count < 0:
            raise ValueError("Active session count cannot be negative")
        self._require(self.sessions_active, "sessions_active").set(count)

    def observe_session_duration(self, minutes: float) -> None:
        """Record session duration in minutes."""
        if minutes < 0:
            raise ValueError(f"Duration cannot be negative: {minutes}")
        self._require(self.session_duration, "session_duration").observe(minutes)

    def increment_reflection(self, status: str) -> None:
        """Increment reflection counter."""
        self._require(self.reflections_generated, "reflections_generated").labels(status=status).inc()

    def observe_reflection_generation(self, seconds: float) -> None:
        """Observe reflection generation time in seconds."""
        if seconds < 0:
            raise ValueError("Generation time cannot be negative")
        self._require(self.reflection_generation_time, "reflection_generation_time").observe(seconds)

    def increment_daily_summary(self, status: str) -> None:
        """Increment daily summary counter."""
        self._require(self.daily_summaries, "daily_summaries").labels(status=status).inc()

    def observe_daily_summary_time(self, seconds: float) -> None:
        """Observe daily summary generation time."""
        if seconds < 0:
            raise ValueError("Summary time cannot be negative")
        self._require(self.daily_summary_time, "daily_summary_time").observe(seconds)

    def increment_learnings(self, count: int = 1) -> None:
        """Increment learnings captured counter."""
        if count < 0:
            raise ValueError("Count cannot be negative")
        self._require(self.learnings_captured, "learnings_captured").inc(count)

    def increment_challenges(self, count: int = 1) -> None:
        """Increment challenges counter."""
        if count < 0:
            raise ValueError("Count cannot be negative")
        self._require(self.challenges_noted, "challenges_noted").inc(count)

    def increment_wins(self, count: int = 1) -> None:
        """Increment wins counter."""
        if count < 0:
            raise ValueError("Count cannot be negative")
        self._require(self.wins_captured, "wins_captured").inc(count)

    def _require(self, metric, name: str):
        """Ensure metric is registered before use."""
        if metric is None:
            raise RuntimeError(f"Metric '{name}' accessed before registration")
        return metric

    def _value(self, metric, **labels: str) -> float:
        """Helper to safely extract metric values."""
        metric_obj = self._require(metric, metric.__class__.__name__ if metric else "metric")
        if labels:
            return metric_obj.labels(**labels)._value.get()
        return metric_obj._value.get()


# Singleton instance
journal_metrics = JournalMetrics()

__all__ = ["JournalMetrics", "journal_metrics"]
