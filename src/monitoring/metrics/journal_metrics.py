"""Journal-specific metrics."""

import time

from prometheus_client import Counter, Gauge, Histogram

from .base import MetricCollector


class JournalMetrics(MetricCollector):
    """Metrics for journal operations."""

    def __init__(self):
        """Initialize journal metrics."""
        super().__init__()
        self.sessions_total = None
        self.sessions_active = None
        self.session_duration = None
        self.reflections_generated_total = None
        self.reflection_generation_seconds = None
        self.learnings_captured_total = None
        self.challenges_noted_total = None
        self.wins_captured_total = None

    def register(self) -> None:
        """Register journal metrics."""
        self.sessions_total = Counter(
            "mcp_journal_sessions_total",
            "Total number of journal sessions",
            ["status"],
            registry=self.registry,
        )

        self.sessions_active = Gauge(
            "mcp_journal_sessions_active",
            "Number of currently active sessions",
            registry=self.registry,
        )

        self.session_duration = Histogram(
            "mcp_journal_session_duration_minutes",
            "Duration of journal sessions in minutes",
            buckets=[1, 5, 10, 30, 60, 120, 240],
            registry=self.registry,
        )

        self.reflections_generated_total = Counter(
            "mcp_journal_reflections_generated_total",
            "Total reflections generated",
            ["status"],
            registry=self.registry,
        )

        self.reflection_generation_seconds = Histogram(
            "mcp_journal_reflection_generation_seconds",
            "Time to generate reflections",
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry,
        )

        self.learnings_captured_total = Counter(
            "mcp_journal_learnings_captured_total",
            "Total learnings captured",
            registry=self.registry,
        )

        self.challenges_noted_total = Counter(
            "mcp_journal_challenges_noted_total",
            "Total challenges noted",
            registry=self.registry,
        )

        self.wins_captured_total = Counter(
            "mcp_journal_wins_captured_total",
            "Total wins captured",
            registry=self.registry,
        )

    def increment_session(self, status: str) -> None:
        """Increment session counter."""
        if self.sessions_total:
            self.sessions_total.labels(status=status).inc()

    def increment_reflection(self, status: str) -> None:
        """Increment reflection generation counter."""
        if self.reflections_generated_total:
            self.reflections_generated_total.labels(status=status).inc()

    def observe_reflection_generation(self, duration: float) -> None:
        """Observe reflection generation time."""
        if self.reflection_generation_seconds:
            self.reflection_generation_seconds.observe(duration)


# Global instance
journal_metrics = JournalMetrics()
