"""Unit tests for metrics functionality."""

import pytest
import asyncio
from prometheus_client import REGISTRY
from src.utils.metrics import (
    journal_sessions_total,
    journal_sessions_active,
    journal_session_duration,
    journal_reflections_generated,
    track_session_operation,
    track_reflection_generation,
    get_metrics
)


class TestMetricsCounters:
    """Test metric counters."""
    
    def test_sessions_total_counter_exists(self):
        """Test sessions total counter is registered."""
        metrics = get_metrics().decode('utf-8')
        assert 'mcp_journal_sessions_total' in metrics
    
    def test_sessions_total_increment(self):
        """Test incrementing sessions counter."""
        initial = journal_sessions_total.labels(status='success')._value.get()
        journal_sessions_total.labels(status='success').inc()
        current = journal_sessions_total.labels(status='success')._value.get()
        assert current == initial + 1
    
    def test_sessions_total_with_labels(self):
        """Test counter with different labels."""
        journal_sessions_total.labels(status='success').inc()
        journal_sessions_total.labels(status='failed').inc()
        
        metrics = get_metrics().decode('utf-8')
        assert 'status="success"' in metrics
        assert 'status="failed"' in metrics
    
    def test_reflections_generated_counter(self):
        """Test reflections counter."""
        initial = journal_reflections_generated.labels(status='success')._value.get()
        journal_reflections_generated.labels(status='success').inc()
        current = journal_reflections_generated.labels(status='success')._value.get()
        assert current == initial + 1


class TestMetricsGauges:
    """Test metric gauges."""
    
    def test_active_sessions_gauge(self):
        """Test active sessions gauge."""
        journal_sessions_active.set(5)
        value = journal_sessions_active._value.get()
        assert value == 5
    
    def test_active_sessions_increment_decrement(self):
        """Test gauge inc/dec."""
        journal_sessions_active.set(0)
        
        journal_sessions_active.inc()
        assert journal_sessions_active._value.get() == 1
        
        journal_sessions_active.inc(3)
        assert journal_sessions_active._value.get() == 4
        
        journal_sessions_active.dec()
        assert journal_sessions_active._value.get() == 3


class TestMetricsHistograms:
    """Test metric histograms."""
    
    def test_session_duration_histogram(self):
        """Test session duration histogram."""
        journal_session_duration.observe(15)
        journal_session_duration.observe(45)
        journal_session_duration.observe(90)
        
        metrics = get_metrics().decode('utf-8')
        assert 'mcp_journal_session_duration_minutes_bucket' in metrics
        assert 'mcp_journal_session_duration_minutes_count' in metrics
        assert 'mcp_journal_session_duration_minutes_sum' in metrics
    
    def test_histogram_buckets(self):
        """Test histogram bucket boundaries."""
        journal_session_duration.observe(10)
        
        metrics = get_metrics().decode('utf-8')
        
        assert 'le="5"' in metrics
        assert 'le="15"' in metrics
        assert 'le="30"' in metrics
        assert 'le="60"' in metrics


class TestMetricDecorators:
    """Test metric decorator functions."""
    
    @pytest.mark.asyncio
    async def test_track_session_operation_success(self):
        """Test session operation tracking on success."""
        @track_session_operation
        async def mock_operation():
            return {"success": True}
        
        initial = journal_sessions_total.labels(status='success')._value.get()
        result = await mock_operation()
        current = journal_sessions_total.labels(status='success')._value.get()
        
        assert current == initial + 1
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_track_session_operation_failure(self):
        """Test session operation tracking on failure."""
        @track_session_operation
        async def mock_operation():
            return {"success": False, "error": "Test error"}
        
        initial = journal_sessions_total.labels(status='failed')._value.get()
        result = await mock_operation()
        current = journal_sessions_total.labels(status='failed')._value.get()
        
        assert current == initial + 1
    
    @pytest.mark.asyncio
    async def test_track_reflection_generation(self):
        """Test reflection generation tracking."""
        @track_reflection_generation
        async def mock_reflection():
            await asyncio.sleep(0.1)
            return {"text": "reflection"}
        
        initial = journal_reflections_generated.labels(status='success')._value.get()
        result = await mock_reflection()
        current = journal_reflections_generated.labels(status='success')._value.get()
        
        assert current == initial + 1
    
    @pytest.mark.asyncio
    async def test_decorator_timing(self):
        """Test that decorator records timing."""
        @track_reflection_generation
        async def mock_slow_operation():
            await asyncio.sleep(0.5)
            return {}
        
        await mock_slow_operation()
        
        metrics = get_metrics().decode('utf-8')
        assert 'mcp_journal_reflection_generation_seconds' in metrics


class TestMetricsExport:
    """Test metrics export functionality."""
    
    def test_get_metrics_format(self):
        """Test metrics are in Prometheus format."""
        metrics = get_metrics()
        
        assert isinstance(metrics, bytes)
        
        metrics_text = metrics.decode('utf-8')
        assert '# HELP' in metrics_text
        assert '# TYPE' in metrics_text
    
    def test_metrics_contains_all_journal_metrics(self):
        """Test all journal metrics are exported."""
        metrics = get_metrics().decode('utf-8')
        
        required_metrics = [
            'mcp_journal_sessions_total',
            'mcp_journal_sessions_active',
            'mcp_journal_session_duration_minutes',
            'mcp_journal_reflections_generated_total',
            'mcp_journal_learnings_captured_total',
            'mcp_journal_challenges_noted_total',
            'mcp_journal_wins_captured_total'
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
