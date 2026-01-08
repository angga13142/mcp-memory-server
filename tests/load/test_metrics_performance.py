"""Load testing for metrics collection and endpoints."""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import psutil
import pytest
import requests


class PerformanceMetrics:
    """Track performance metrics during load tests."""

    def __init__(self):
        self.response_times: list[float] = []
        self.success_count: int = 0
        self.failure_count: int = 0
        self.cpu_samples: list[float] = []
        self.memory_samples: list[float] = []

    def record_response(self, duration: float, success: bool):
        """Record a response time."""
        self.response_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def record_system_metrics(self):
        """Record current system metrics."""
        process = psutil.Process()
        self.cpu_samples.append(process.cpu_percent())
        self.memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB

    def get_statistics(self) -> dict:
        """Calculate statistics."""
        if not self.response_times:
            return {}

        sorted_times = sorted(self.response_times)
        return {
            "total_requests": len(self.response_times),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / len(self.response_times) * 100,
            "min_ms": min(self.response_times) * 1000,
            "max_ms": max(self.response_times) * 1000,
            "mean_ms": statistics.mean(self.response_times) * 1000,
            "median_ms": statistics.median(self.response_times) * 1000,
            "p95_ms": sorted_times[int(len(sorted_times) * 0.95)] * 1000,
            "p99_ms": sorted_times[int(len(sorted_times) * 0.99)] * 1000,
            "avg_cpu_percent": (
                statistics.mean(self.cpu_samples) if self.cpu_samples else 0
            ),
            "max_cpu_percent": max(self.cpu_samples) if self.cpu_samples else 0,
            "avg_memory_mb": (
                statistics.mean(self.memory_samples) if self.memory_samples else 0
            ),
            "max_memory_mb": max(self.memory_samples) if self.memory_samples else 0,
        }

    def print_report(self):
        """Print performance report."""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("LOAD TEST PERFORMANCE REPORT")
        print("=" * 60)
        print(f"Total Requests:      {stats. get('total_requests', 0)}")
        print(f"Success Rate:       {stats.get('success_rate', 0):.2f}%")
        print(f"Failures:           {stats.get('failure_count', 0)}")
        print()
        print("Response Times (ms):")
        print(f"  Min:              {stats.get('min_ms', 0):.2f}")
        print(f"  Mean:             {stats.get('mean_ms', 0):.2f}")
        print(f"  Median:           {stats. get('median_ms', 0):.2f}")
        print(f"  P95:              {stats.get('p95_ms', 0):.2f}")
        print(f"  P99:              {stats.get('p99_ms', 0):.2f}")
        print(f"  Max:              {stats.get('max_ms', 0):.2f}")
        print()
        print("Resource Usage:")
        print(f"  Avg CPU:          {stats.get('avg_cpu_percent', 0):.2f}%")
        print(f"  Max CPU:          {stats.get('max_cpu_percent', 0):.2f}%")
        print(f"  Avg Memory:       {stats.get('avg_memory_mb', 0):.2f} MB")
        print(f"  Max Memory:       {stats. get('max_memory_mb', 0):.2f} MB")
        print("=" * 60)
        print()


@pytest.mark.load
class TestMetricsEndpointLoad:
    """Load tests for /metrics endpoint."""

    @pytest.fixture
    def metrics_url(self):
        """Metrics endpoint URL."""
        return "http://localhost:8081"

    def test_metrics_endpoint_concurrent_requests(self, metrics_url):
        """Test metrics endpoint with concurrent requests."""
        print("\n🔥 Test:  Concurrent Metrics Endpoint Requests")

        perf = PerformanceMetrics()
        num_requests = 100
        num_workers = 10

        def fetch_metrics():
            start = time.time()
            try:
                response = requests.get(metrics_url, timeout=5)
                duration = time.time() - start
                success = response.status_code == 200
                perf.record_response(duration, success)
                return success
            except Exception:
                duration = time.time() - start
                perf.record_response(duration, False)
                return False

        # Execute concurrent requests
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(fetch_metrics) for _ in range(num_requests)]
            [f.result() for f in futures]

        total_duration = time.time() - start_time

        # Print results
        perf.print_report()
        print(f"Total Duration:     {total_duration:.2f}s")
        print(f"Requests/Second:    {num_requests/total_duration:.2f}")

        # Assertions
        stats = perf.get_statistics()
        assert (
            stats["success_rate"] > 99
        ), f"Success rate too low: {stats['success_rate']}%"
        assert stats["p95_ms"] < 100, f"P95 response time too high: {stats['p95_ms']}ms"
        assert (
            stats["mean_ms"] < 50
        ), f"Mean response time too high: {stats['mean_ms']}ms"

    def test_metrics_endpoint_sustained_load(self, metrics_url):
        """Test metrics endpoint under sustained load."""
        print("\n🔥 Test: Sustained Load on Metrics Endpoint")

        perf = PerformanceMetrics()
        duration_seconds = 30
        requests_per_second = 10

        def fetch_with_monitoring():
            start = time.time()
            try:
                response = requests.get(metrics_url, timeout=5)
                duration = time.time() - start
                success = response.status_code == 200
                perf.record_response(duration, success)
                perf.record_system_metrics()
                return success
            except Exception:
                duration = time.time() - start
                perf.record_response(duration, False)
                return False

        # Run for specified duration
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration_seconds:
            fetch_with_monitoring()
            request_count += 1

            # Maintain rate
            elapsed = time.time() - start_time
            expected_requests = elapsed * requests_per_second
            if request_count > expected_requests:
                time.sleep((request_count - expected_requests) / requests_per_second)

        # Print results
        perf.print_report()

        # Assertions
        stats = perf.get_statistics()
        assert (
            stats["success_rate"] > 99
        ), f"Success rate degraded: {stats['success_rate']}%"
        assert stats["p95_ms"] < 100, f"P95 response time too high: {stats['p95_ms']}ms"
        assert (
            stats["max_cpu_percent"] < 50
        ), f"CPU usage too high: {stats['max_cpu_percent']}%"

    def test_metrics_endpoint_burst_traffic(self, metrics_url):
        """Test metrics endpoint with burst traffic."""
        print("\n🔥 Test: Burst Traffic on Metrics Endpoint")

        perf = PerformanceMetrics()

        # Normal load
        print("Phase 1: Normal load (10 req/s for 5s)...")
        for _ in range(50):
            start = time.time()
            try:
                response = requests.get(metrics_url, timeout=5)
                perf.record_response(time.time() - start, response.status_code == 200)
            except Exception:
                perf.record_response(time.time() - start, False)
            time.sleep(0.1)

        # Burst
        print("Phase 2: Burst (100 concurrent requests)...")

        def fetch():
            start = time.time()
            try:
                response = requests.get(metrics_url, timeout=10)
                return time.time() - start, response.status_code == 200
            except Exception:
                return time.time() - start, False

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch) for _ in range(100)]
            for future in futures:
                duration, success = future.result()
                perf.record_response(duration, success)

        # Recovery
        print("Phase 3: Recovery (10 req/s for 5s)...")
        for _ in range(50):
            start = time.time()
            try:
                response = requests.get(metrics_url, timeout=5)
                perf.record_response(time.time() - start, response.status_code == 200)
            except Exception:
                perf.record_response(time.time() - start, False)
            time.sleep(0.1)

        # Print results
        perf.print_report()

        # Assertions
        stats = perf.get_statistics()
        assert (
            stats["success_rate"] > 95
        ), f"Success rate too low:  {stats['success_rate']}%"
        assert (
            stats["p99_ms"] < 500
        ), f"P99 response time too high during burst: {stats['p99_ms']}ms"


@pytest.mark.load
class TestMetricCollectionLoad:
    """Load tests for metric collection operations."""

    @pytest.mark.asyncio
    async def test_high_frequency_metric_updates(self):
        """Test high-frequency metric updates."""
        print("\n🔥 Test: High-Frequency Metric Updates")

        from src.monitoring.metrics import journal_metrics

        perf = PerformanceMetrics()
        num_updates = 10000

        # Measure baseline
        process = psutil.Process()
        baseline_cpu = process.cpu_percent(interval=1)
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Perform updates
        start_time = time.time()

        for i in range(num_updates):
            update_start = time.time()

            # Simulate metric updates
            journal_metrics.sessions_total.labels(status="success").inc()
            journal_metrics.sessions_active.set(i % 10)
            journal_metrics.session_duration.observe(i % 100)

            update_duration = time.time() - update_start
            perf.record_response(update_duration, True)

            # Sample system metrics periodically
            if i % 1000 == 0:
                perf.record_system_metrics()

        total_duration = time.time() - start_time

        # Measure after
        after_cpu = process.cpu_percent(interval=1)
        after_memory = process.memory_info().rss / 1024 / 1024

        # Print results
        perf.print_report()
        print(f"Updates/Second:      {num_updates/total_duration:.2f}")
        print(f"CPU Overhead:       {after_cpu - baseline_cpu:.2f}%")
        print(f"Memory Overhead:    {after_memory - baseline_memory:.2f} MB")

        # Assertions
        stats = perf.get_statistics()
        assert stats["mean_ms"] < 1, f"Mean update time too high: {stats['mean_ms']}ms"
        assert stats["p99_ms"] < 5, f"P99 update time too high: {stats['p99_ms']}ms"
        assert (
            after_cpu - baseline_cpu
        ) < 10, f"CPU overhead too high:  {after_cpu - baseline_cpu}%"
        assert (
            after_memory - baseline_memory
        ) < 100, f"Memory overhead too high:  {after_memory - baseline_memory}MB"

    @pytest.mark.asyncio
    async def test_concurrent_metric_updates(self):
        """Test concurrent metric updates from multiple tasks."""
        print("\n🔥 Test: Concurrent Metric Updates")

        from src.monitoring.metrics import journal_metrics

        perf = PerformanceMetrics()
        num_tasks = 50
        updates_per_task = 100

        async def update_metrics(task_id: int):
            """Update metrics concurrently."""
            for i in range(updates_per_task):
                start = time.time()

                journal_metrics.sessions_total.labels(status="success").inc()
                journal_metrics.sessions_active.set(task_id)
                journal_metrics.session_duration.observe(i)

                duration = time.time() - start
                perf.record_response(duration, True)

                # Small delay to simulate real work
                await asyncio.sleep(0.001)

        # Execute concurrent tasks
        start_time = time.time()

        tasks = [update_metrics(i) for i in range(num_tasks)]
        await asyncio.gather(*tasks)

        total_duration = time.time() - start_time
        total_updates = num_tasks * updates_per_task

        # Print results
        perf.print_report()
        print(f"Total Updates:      {total_updates}")
        print(f"Updates/Second:     {total_updates/total_duration:.2f}")
        print(f"Concurrent Tasks:   {num_tasks}")

        # Assertions
        stats = perf.get_statistics()
        assert (
            stats["success_rate"] == 100
        ), f"Some updates failed: {stats['failure_count']}"
        assert stats["p95_ms"] < 10, f"P95 update time too high: {stats['p95_ms']}ms"

    @pytest.mark.asyncio
    async def test_metric_collection_under_load(self):
        """Test metric collection while application is under load."""
        print("\n🔥 Test:  Metric Collection Under Application Load")

        from src.monitoring.metrics import journal_metrics, system_metrics

        perf = PerformanceMetrics()

        # Start background load
        async def background_load():
            """Simulate application load."""
            for i in range(1000):
                journal_metrics.sessions_total.labels(status="success").inc()
                journal_metrics.sessions_active.set(i % 20)
                await asyncio.sleep(0.01)

        load_task = asyncio.create_task(background_load())

        # Collect metrics while under load
        for _ in range(20):
            start = time.time()

            # Collect all metrics
            system_metrics.collect()
            journal_metrics.collect()

            duration = time.time() - start
            perf.record_response(duration, True)
            perf.record_system_metrics()

            await asyncio.sleep(0.5)

        # Wait for background load to complete
        await load_task

        # Print results
        perf.print_report()

        # Assertions
        stats = perf.get_statistics()
        assert (
            stats["mean_ms"] < 50
        ), f"Mean collection time too high: {stats['mean_ms']}ms"
        assert (
            stats["p95_ms"] < 100
        ), f"P95 collection time too high: {stats['p95_ms']}ms"


@pytest.mark.load
class TestPrometheusScrapingLoad:
    """Load tests for Prometheus scraping."""

    def test_prometheus_scrape_during_high_load(self):
        """Test Prometheus scraping while metrics endpoint is under load."""
        print("\n🔥 Test:  Prometheus Scraping During High Load")

        metrics_url = "http://localhost:8081"
        prometheus_url = "http://localhost:9090/api/v1/query"

        # Skip if Prometheus is not available
        try:
            requests.get(prometheus_url, timeout=1)
        except requests.exceptions.RequestException:
            pytest.skip("Prometheus not available at localhost:9090")

        perf_app = PerformanceMetrics()
        perf_prom = PerformanceMetrics()

        # Start application load
        def generate_app_load():
            for _ in range(100):
                start = time.time()
                try:
                    response = requests.get(metrics_url, timeout=5)
                    perf_app.record_response(
                        time.time() - start, response.status_code == 200
                    )
                except Exception:
                    perf_app.record_response(time.time() - start, False)
                time.sleep(0.1)

        # Start Prometheus queries
        def query_prometheus():
            for _ in range(10):
                start = time.time()
                try:
                    response = requests.get(
                        prometheus_url,
                        params={"query": "mcp_journal_sessions_total"},
                        timeout=5,
                    )
                    perf_prom.record_response(
                        time.time() - start, response.status_code == 200
                    )
                except Exception:
                    perf_prom.record_response(time.time() - start, False)
                time.sleep(1)

        # Run concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            app_future = executor.submit(generate_app_load)
            prom_future = executor.submit(query_prometheus)

            app_future.result()
            prom_future.result()

        # Print results
        print("\nApplication Metrics Endpoint:")
        perf_app.print_report()

        print("\nPrometheus Queries:")
        perf_prom.print_report()

        # Assertions
        app_stats = perf_app.get_statistics()
        prom_stats = perf_prom.get_statistics()

        assert (
            app_stats["success_rate"] > 99
        ), f"App endpoint success rate too low: {app_stats['success_rate']}%"
        assert (
            prom_stats["success_rate"] == 100
        ), f"Prometheus queries failed: {prom_stats['failure_count']}"
        assert (
            app_stats["p95_ms"] < 100
        ), f"App endpoint P95 too high: {app_stats['p95_ms']}ms"


@pytest.mark.load
class TestEndToEndLoad:
    """End-to-end load tests."""

    @pytest.mark.asyncio
    async def test_full_system_under_load(self):
        """Test entire monitoring stack under load."""
        print("\n🔥 Test: Full System Under Load")

        from src.monitoring.metrics import journal_metrics, system_metrics

        perf = PerformanceMetrics()
        duration_seconds = 60

        print(f"Running full system load test for {duration_seconds} seconds...")
        print("Generating:  sessions, reflections, database queries, system metrics")

        async def simulate_session_activity():
            """Simulate work session activity."""
            for _i in range(200):
                # Start session
                journal_metrics.sessions_total.labels(status="success").inc()
                journal_metrics.sessions_active.inc()

                # Simulate work
                await asyncio.sleep(0.1)

                # Generate reflection
                journal_metrics.reflections_generated_total.labels(
                    status="success"
                ).inc()
                journal_metrics.reflection_generation_seconds.observe(0.5)

                # Add learnings
                journal_metrics.learnings_captured_total.inc()

                # End session
                journal_metrics.sessions_active.dec()
                journal_metrics.session_duration.observe(30)

                await asyncio.sleep(0.2)

        async def collect_system_metrics():
            """Collect system metrics periodically."""
            for _ in range(int(duration_seconds / 15)):
                start = time.time()
                system_metrics.collect()
                duration = time.time() - start
                perf.record_response(duration, True)
                perf.record_system_metrics()
                await asyncio.sleep(15)

        async def query_metrics_endpoint():
            """Query metrics endpoint periodically."""
            for _ in range(int(duration_seconds / 2)):
                start = time.time()
                try:
                    response = requests.get("http://localhost:8081", timeout=5)
                    duration = time.time() - start
                    perf.record_response(duration, response.status_code == 200)
                except Exception:
                    perf.record_response(time.time() - start, False)
                await asyncio.sleep(2)

        # Run all tasks concurrently
        start_time = time.time()

        await asyncio.gather(
            simulate_session_activity(),
            collect_system_metrics(),
            query_metrics_endpoint(),
        )

        total_duration = time.time() - start_time

        # Print results
        perf.print_report()
        print(f"Test Duration:      {total_duration:.2f}s")

        # Assertions
        stats = perf.get_statistics()
        assert (
            stats["success_rate"] > 99
        ), f"Success rate too low: {stats['success_rate']}%"
        assert (
            stats["avg_cpu_percent"] < 30
        ), f"Average CPU too high: {stats['avg_cpu_percent']}%"
        assert (
            stats["max_cpu_percent"] < 50
        ), f"Max CPU too high:  {stats['max_cpu_percent']}%"


# Utility function to run all load tests
def run_all_load_tests():
    """Run all load tests and generate report."""
    print("\n" + "=" * 60)
    print("RUNNING ALL LOAD TESTS")
    print("=" * 60)

    pytest.main(
        ["tests/load/test_metrics_performance.py", "-v", "-m", "load", "--tb=short"]
    )
