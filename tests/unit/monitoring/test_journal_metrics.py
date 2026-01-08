"""Unit tests for journal metrics."""

import pytest
from prometheus_client import CollectorRegistry

from src.monitoring.metrics.journal_metrics import JournalMetrics


class TestJournalMetrics:
    """Test JournalMetrics class."""

    @pytest.fixture
    def metrics(self):
        """Create JournalMetrics instance with isolated registry."""
        m = JournalMetrics()
        m.registry = CollectorRegistry()
        m.register()
        return m

    def test_register_creates_all_metrics(self, metrics):
        """Test that register creates all 8 metrics."""
        assert metrics.sessions_total is not None
        assert metrics.sessions_active is not None
        assert metrics.session_duration is not None
        assert metrics.reflections_generated_total is not None
        assert metrics.reflection_generation_seconds is not None
        assert metrics.learnings_captured_total is not None
        assert metrics.challenges_noted_total is not None
        assert metrics.wins_captured_total is not None

    def test_sessions_total_increment(self, metrics):
        """Test incrementing total sessions counter."""
        initial = metrics.sessions_total.labels(status="success")._value.get()

        metrics.sessions_total.labels(status="success").inc()

        final = metrics.sessions_total.labels(status="success")._value.get()
        assert final == initial + 1

    def test_sessions_active_gauge(self, metrics):
        """Test setting active sessions gauge."""
        metrics.sessions_active.set(5)

        value = metrics.sessions_active._value.get()
        assert value == 5

    def test_sessions_active_inc_dec(self, metrics):
        """Test incrementing and decrementing active sessions."""
        metrics.sessions_active.set(0)
        metrics.sessions_active.inc()
        assert metrics.sessions_active._value.get() == 1

        metrics.sessions_active.inc()
        assert metrics.sessions_active._value.get() == 2

        metrics.sessions_active.dec()
        assert metrics.sessions_active._value.get() == 1

    def test_session_duration_observation(self, metrics):
        """Test observing session duration."""
        metrics.session_duration.observe(30)

        # Check histogram was updated
        assert metrics.session_duration._sum.get() > 0

    def test_reflection_generation_tracking(self, metrics):
        """Test reflection generation metrics."""
        # Success
        metrics.reflections_generated_total.labels(status="success").inc()

        # Duration
        metrics.reflection_generation_seconds.observe(2.5)

        assert (
            metrics.reflections_generated_total.labels(status="success")._value.get()
            > 0
        )
        assert metrics.reflection_generation_seconds._sum.get() > 0

    def test_learning_tracking(self, metrics):
        """Test learning capture metrics."""
        metrics.learnings_captured_total.inc()
        metrics.challenges_noted_total.inc()
        metrics.wins_captured_total.inc()

        assert metrics.learnings_captured_total._value.get() == 1
        assert metrics.challenges_noted_total._value.get() == 1
        assert metrics.wins_captured_total._value.get() == 1

    def test_multiple_status_labels(self, metrics):
        """Test metrics with different status labels."""
        metrics.sessions_total.labels(status="success").inc()
        metrics.sessions_total.labels(status="error").inc()

        success_count = metrics.sessions_total.labels(status="success")._value.get()
        error_count = metrics.sessions_total.labels(status="error")._value.get()

        assert success_count >= 1
        assert error_count >= 1

    def test_increment_session_method(self, metrics):
        """Test the increment_session helper method."""
        metrics.increment_session("success")
        metrics.increment_session("success")
        metrics.increment_session("error")

        assert metrics.sessions_total.labels(status="success")._value.get() == 2
        assert metrics.sessions_total.labels(status="error")._value.get() == 1

    def test_increment_reflection_method(self, metrics):
        """Test the increment_reflection helper method."""
        metrics.increment_reflection("success")
        metrics.increment_reflection("error")

        assert (
            metrics.reflections_generated_total.labels(status="success")._value.get()
            == 1
        )
        assert (
            metrics.reflections_generated_total.labels(status="error")._value.get() == 1
        )

    def test_observe_reflection_generation_method(self, metrics):
        """Test the observe_reflection_generation helper method."""
        metrics.observe_reflection_generation(1.5)
        metrics.observe_reflection_generation(2.5)

        assert metrics.reflection_generation_seconds._sum.get() == 4.0

    def test_histogram_buckets(self, metrics):
        """Test that histogram has proper buckets."""
        # Session duration buckets: [1, 5, 10, 30, 60, 120, 240]
        metrics.session_duration.observe(2)  # Falls in 5 bucket
        metrics.session_duration.observe(45)  # Falls in 60 bucket

        # Just verify observation works without error
        assert metrics.session_duration._sum.get() == 47
