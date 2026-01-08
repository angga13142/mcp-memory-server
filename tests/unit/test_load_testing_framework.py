"""Unit tests for load testing framework components."""

import time

from tests.load.test_metrics_performance import PerformanceMetrics


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_initialization(self):
        """Test PerformanceMetrics initialization."""
        perf = PerformanceMetrics()

        assert perf.response_times == []
        assert perf.success_count == 0
        assert perf.failure_count == 0
        assert perf.cpu_samples == []
        assert perf.memory_samples == []

    def test_record_response_success(self):
        """Test recording successful response."""
        perf = PerformanceMetrics()

        perf.record_response(0.050, True)  # 50ms, success

        assert len(perf.response_times) == 1
        assert perf.response_times[0] == 0.050
        assert perf.success_count == 1
        assert perf.failure_count == 0

    def test_record_response_failure(self):
        """Test recording failed response."""
        perf = PerformanceMetrics()

        perf.record_response(1.000, False)  # 1000ms, failed

        assert len(perf.response_times) == 1
        assert perf.success_count == 0
        assert perf.failure_count == 1

    def test_record_multiple_responses(self):
        """Test recording multiple responses."""
        perf = PerformanceMetrics()

        perf.record_response(0.010, True)
        perf.record_response(0.020, True)
        perf.record_response(0.030, False)
        perf.record_response(0.040, True)

        assert len(perf.response_times) == 4
        assert perf.success_count == 3
        assert perf.failure_count == 1

    def test_record_system_metrics(self):
        """Test recording system metrics."""
        perf = PerformanceMetrics()

        perf.record_system_metrics()

        assert len(perf.cpu_samples) == 1
        assert len(perf.memory_samples) == 1
        assert perf.cpu_samples[0] >= 0
        assert perf.memory_samples[0] > 0

    def test_get_statistics_empty(self):
        """Test getting statistics with no data."""
        perf = PerformanceMetrics()

        stats = perf.get_statistics()

        assert stats == {}

    def test_get_statistics_single_response(self):
        """Test getting statistics with single response."""
        perf = PerformanceMetrics()
        perf.record_response(0.050, True)

        stats = perf.get_statistics()

        assert stats["total_requests"] == 1
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 0
        assert stats["success_rate"] == 100.0
        assert stats["min_ms"] == 50.0
        assert stats["max_ms"] == 50.0
        assert stats["mean_ms"] == 50.0
        assert stats["median_ms"] == 50.0

    def test_get_statistics_multiple_responses(self):
        """Test getting statistics with multiple responses."""
        perf = PerformanceMetrics()

        # Add various response times
        response_times = [
            0.010,
            0.020,
            0.030,
            0.040,
            0.050,
            0.060,
            0.070,
            0.080,
            0.090,
            0.100,
        ]

        for i, rt in enumerate(response_times):
            perf.record_response(rt, i % 10 != 9)  # 1 failure

        stats = perf.get_statistics()

        assert stats["total_requests"] == 10
        assert stats["success_count"] == 9
        assert stats["failure_count"] == 1
        assert stats["success_rate"] == 90.0
        assert stats["min_ms"] == 10.0
        assert stats["max_ms"] == 100.0
        assert 50.0 <= stats["mean_ms"] <= 60.0
        assert stats["median_ms"] == 55.0

    def test_percentile_calculations(self):
        """Test percentile calculations are accurate."""
        perf = PerformanceMetrics()

        # Add 100 responses from 0.001 to 0.100
        for i in range(100):
            perf.record_response(0.001 * (i + 1), True)

        stats = perf.get_statistics()

        # P95 should be around 95ms
        assert 94.0 <= stats["p95_ms"] <= 96.0

        # P99 should be around 99ms
        assert 98.0 <= stats["p99_ms"] <= 100.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        perf = PerformanceMetrics()

        # 95 successes, 5 failures
        for i in range(100):
            perf.record_response(0.010, i < 95)

        stats = perf.get_statistics()

        assert stats["success_rate"] == 95.0
        assert stats["success_count"] == 95
        assert stats["failure_count"] == 5

    def test_system_metrics_statistics(self):
        """Test system metrics in statistics."""
        perf = PerformanceMetrics()

        # Record some responses and system metrics
        for _ in range(10):
            perf.record_response(0.010, True)
            perf.record_system_metrics()

        stats = perf.get_statistics()

        assert "avg_cpu_percent" in stats
        assert "max_cpu_percent" in stats
        assert "avg_memory_mb" in stats
        assert "max_memory_mb" in stats
        assert stats["avg_cpu_percent"] >= 0
        assert stats["max_cpu_percent"] >= stats["avg_cpu_percent"]
        assert stats["avg_memory_mb"] > 0
        assert stats["max_memory_mb"] >= stats["avg_memory_mb"]

    def test_print_report_runs(self):
        """Test that print_report doesn't crash."""
        perf = PerformanceMetrics()

        for i in range(10):
            perf.record_response(0.010 * (i + 1), True)
            perf.record_system_metrics()

        # Should not raise exception
        perf.print_report()


class TestLoadTestHelpers:
    """Test helper functions for load testing."""

    def test_concurrent_execution_timing(self):
        """Test that concurrent execution improves throughput."""
        import concurrent.futures

        def slow_task():
            time.sleep(0.1)
            return True

        # Sequential execution
        start = time.time()
        for _ in range(10):
            slow_task()
        sequential_time = time.time() - start

        # Concurrent execution
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(slow_task) for _ in range(10)]
            results = [f.result() for f in futures]
        concurrent_time = time.time() - start

        # Concurrent should be significantly faster
        assert concurrent_time < sequential_time / 2
        assert all(results)

    def test_rate_limiting(self):
        """Test rate limiting for sustained load."""
        requests_per_second = 10
        duration_seconds = 2
        expected_requests = requests_per_second * duration_seconds

        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration_seconds:
            # Simulate request
            request_count += 1

            # Rate limiting
            elapsed = time.time() - start_time
            expected = elapsed * requests_per_second
            if request_count > expected:
                time.sleep((request_count - expected) / requests_per_second)

        actual_duration = time.time() - start_time
        actual_rate = request_count / actual_duration

        # Should be close to target rate
        assert expected_requests - 2 <= request_count <= expected_requests + 2
        assert 9 <= actual_rate <= 11  # 10 ± 1 req/s


class TestLoadTestScenarios:
    """Test that load test scenarios are correctly implemented."""

    def test_burst_traffic_pattern(self):
        """Test burst traffic pattern simulation."""
        perf = PerformanceMetrics()

        # Phase 1: Normal load
        for _ in range(10):
            perf.record_response(0.020, True)

        # Phase 2: Burst (slower responses expected)
        for _ in range(50):
            perf.record_response(0.100, True)  # Slower during burst

        # Phase 3: Recovery
        for _ in range(10):
            perf.record_response(0.020, True)

        stats = perf.get_statistics()

        assert stats["total_requests"] == 70
        assert stats["success_rate"] == 100.0

        # Max should reflect burst slowdown
        assert stats["max_ms"] >= 100.0

    def test_sustained_load_pattern(self):
        """Test sustained load pattern."""
        perf = PerformanceMetrics()

        # Simulate sustained load with consistent performance
        for _ in range(100):
            perf.record_response(0.030, True)
            perf.record_system_metrics()

        stats = perf.get_statistics()

        # Should maintain consistent performance
        assert stats["success_rate"] == 100.0

        # Response times should be consistent
        variance = stats["max_ms"] - stats["min_ms"]
        assert variance < 10.0  # Low variance under sustained load


class TestPerformanceAssertions:
    """Test performance assertion helpers."""

    def test_assert_response_time_target(self):
        """Test response time assertions."""
        perf = PerformanceMetrics()

        # All responses under 100ms
        for _i in range(100):
            perf.record_response(0.050, True)

        stats = perf.get_statistics()

        # Should pass 100ms target
        assert stats["p95_ms"] < 100
        assert stats["p99_ms"] < 100

    def test_assert_success_rate_target(self):
        """Test success rate assertions."""
        perf = PerformanceMetrics()

        # 99% success rate
        for i in range(100):
            perf.record_response(0.010, i < 99)

        stats = perf.get_statistics()

        # Should meet 99% target
        assert stats["success_rate"] >= 99.0

    def test_assert_cpu_overhead_target(self):
        """Test CPU overhead assertions."""
        import psutil

        process = psutil.Process()

        # Get baseline
        baseline = process.cpu_percent(interval=1)

        # Simulate light load
        time.sleep(0.5)

        # Measure overhead
        current = process.cpu_percent(interval=1)
        overhead = current - baseline

        # Should be minimal
        assert overhead < 10  # Less than 10% overhead


class TestLoadTestReporting:
    """Test load test reporting functionality."""

    def test_report_generation(self):
        """Test that reports can be generated."""
        perf = PerformanceMetrics()

        for i in range(50):
            perf.record_response(0.020 * (i % 10 + 1), i % 20 != 0)
            if i % 5 == 0:
                perf.record_system_metrics()

        stats = perf.get_statistics()

        # Verify all required fields present
        required_fields = [
            "total_requests",
            "success_count",
            "failure_count",
            "success_rate",
            "min_ms",
            "max_ms",
            "mean_ms",
            "median_ms",
            "p95_ms",
            "p99_ms",
        ]

        for field in required_fields:
            assert field in stats, f"Missing field: {field}"
            assert stats[field] is not None

    def test_report_formatting(self):
        """Test that report can be formatted properly."""
        perf = PerformanceMetrics()

        for _i in range(10):
            perf.record_response(0.025, True)
            perf.record_system_metrics()

        # Should not raise exception
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        perf.print_report()

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        # Verify output contains key sections
        assert "LOAD TEST PERFORMANCE REPORT" in output
        assert "Total Requests:" in output
        assert "Response Times" in output
        assert "Resource Usage:" in output
