"""Unit tests for monitoring decorators."""

import asyncio
import time

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram

from src.monitoring.decorators import count_calls, track_time


class TestTrackTimeDecorator:
    """Test @track_time decorator."""

    @pytest.fixture
    def histogram(self):
        """Create test histogram."""
        registry = CollectorRegistry()
        return Histogram("test_duration_seconds", "Test duration", registry=registry)

    @pytest.fixture
    def labeled_histogram(self):
        """Create test histogram with labels."""
        registry = CollectorRegistry()
        return Histogram(
            "test_labeled_duration", "Test duration", ["operation"], registry=registry
        )

    def test_track_time_decorator(self, histogram):
        """Test @track_time decorator tracks duration."""

        @track_time(histogram)
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()

        assert result == "done"
        assert histogram._sum.get() >= 0.1

    def test_track_time_with_labels(self, labeled_histogram):
        """Test @track_time with labels."""

        @track_time(labeled_histogram, labels={"operation": "test"})
        def labeled_function():
            time.sleep(0.05)
            return "labeled"

        result = labeled_function()

        assert result == "labeled"
        assert labeled_histogram.labels(operation="test")._sum.get() >= 0.05

    def test_track_time_preserves_exceptions(self, histogram):
        """Test that @track_time preserves exceptions."""

        @track_time(histogram)
        def failing_function():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_function()

        # Should still record the duration
        assert histogram._sum.get() >= 0

    @pytest.mark.asyncio
    async def test_track_time_async(self, histogram):
        """Test @track_time with async function."""

        @track_time(histogram)
        async def async_slow_function():
            await asyncio.sleep(0.1)
            return "async done"

        result = await async_slow_function()

        assert result == "async done"
        assert histogram._sum.get() >= 0.1

    @pytest.mark.asyncio
    async def test_track_time_async_with_labels(self, labeled_histogram):
        """Test @track_time async with labels."""

        @track_time(labeled_histogram, labels={"operation": "async_test"})
        async def async_labeled():
            await asyncio.sleep(0.05)
            return "async labeled"

        result = await async_labeled()

        assert result == "async labeled"
        assert labeled_histogram.labels(operation="async_test")._sum.get() >= 0.05

    @pytest.mark.asyncio
    async def test_track_time_async_preserves_exceptions(self, histogram):
        """Test that @track_time preserves async exceptions."""

        @track_time(histogram)
        async def async_failing():
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError, match="async error"):
            await async_failing()


class TestCountCallsDecorator:
    """Test @count_calls decorator."""

    @pytest.fixture
    def counter(self):
        """Create test counter."""
        registry = CollectorRegistry()
        return Counter("test_calls_total", "Test calls", ["status"], registry=registry)

    @pytest.fixture
    def labeled_counter(self):
        """Create test counter with additional labels."""
        registry = CollectorRegistry()
        return Counter(
            "test_labeled_calls",
            "Test calls",
            ["operation", "status"],
            registry=registry,
        )

    def test_count_calls_success(self, counter):
        """Test @count_calls increments on success."""

        @count_calls(counter)
        def successful_function():
            return "success"

        result = successful_function()

        assert result == "success"
        assert counter.labels(status="success")._value.get() == 1

    def test_count_calls_error(self, counter):
        """Test @count_calls increments error on exception."""

        @count_calls(counter)
        def failing_function():
            raise ValueError("error")

        with pytest.raises(ValueError):
            failing_function()

        assert counter.labels(status="error")._value.get() == 1

    def test_count_calls_multiple(self, counter):
        """Test @count_calls counts multiple calls."""

        @count_calls(counter)
        def multi_function():
            return "ok"

        for _ in range(5):
            multi_function()

        assert counter.labels(status="success")._value.get() == 5

    def test_count_calls_with_labels(self, labeled_counter):
        """Test @count_calls with additional labels."""

        @count_calls(labeled_counter, labels={"operation": "read"})
        def labeled_function():
            return "read success"

        result = labeled_function()

        assert result == "read success"
        assert (
            labeled_counter.labels(operation="read", status="success")._value.get() == 1
        )

    @pytest.mark.asyncio
    async def test_count_calls_async_success(self, counter):
        """Test @count_calls with async function."""

        @count_calls(counter)
        async def async_function():
            await asyncio.sleep(0.01)
            return "async success"

        result = await async_function()

        assert result == "async success"
        assert counter.labels(status="success")._value.get() == 1

    @pytest.mark.asyncio
    async def test_count_calls_async_error(self, counter):
        """Test @count_calls async increments error on exception."""

        @count_calls(counter)
        async def async_failing():
            raise RuntimeError("async error")

        with pytest.raises(RuntimeError):
            await async_failing()

        assert counter.labels(status="error")._value.get() == 1

    def test_count_calls_mixed_success_error(self, counter):
        """Test @count_calls tracks both success and error."""

        @count_calls(counter)
        def sometimes_fails(should_fail: bool):
            if should_fail:
                raise ValueError("failed")
            return "success"

        # Some successes
        sometimes_fails(False)
        sometimes_fails(False)

        # Some failures
        with pytest.raises(ValueError):
            sometimes_fails(True)

        assert counter.labels(status="success")._value.get() == 2
        assert counter.labels(status="error")._value.get() == 1


class TestDecoratorCombination:
    """Test combining decorators."""

    def test_track_time_and_count_calls(self):
        """Test using both decorators together."""
        registry = CollectorRegistry()
        histogram = Histogram("combo_duration", "Duration", registry=registry)
        counter = Counter("combo_calls", "Calls", ["status"], registry=registry)

        @track_time(histogram)
        @count_calls(counter)
        def combined_function():
            time.sleep(0.05)
            return "combined"

        result = combined_function()

        assert result == "combined"
        assert histogram._sum.get() >= 0.05
        assert counter.labels(status="success")._value.get() == 1
