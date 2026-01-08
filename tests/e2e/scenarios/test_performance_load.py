"""E2E test for performance under load."""

import concurrent.futures
import time

import pytest
import requests

from tests.e2e.base import APIClient, E2ETestBase, PrometheusClient


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.load
class TestPerformanceLoadE2E(E2ETestBase):
    """Test system performance under load."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """API client."""
        return APIClient()

    @pytest.fixture(scope="class")
    def prometheus_client(self):
        """Prometheus client."""
        return PrometheusClient()

    @pytest.fixture(scope="class", autouse=True)
    def ensure_app_available(self):
        """Ensure application is running."""
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Application not healthy")
        except requests.exceptions.RequestException:
            pytest.skip("Application not available")

    def test_sustained_load_performance(self, api_client, prometheus_client):
        """
        Test system under sustained load:
        1. Get baseline performance
        2. Generate sustained load
        3. Verify performance targets
        """
        print("\n🔥 Starting Sustained Load E2E Test")

        # Step 1: Get baseline
        def get_baseline():
            times = []
            for _ in range(5):
                start = time.time()
                api_client.get("/metrics")
                times.append(time.time() - start)

            return {
                "avg_response_time": sum(times) / len(times),
                "max_response_time": max(times),
            }

        baseline = self.execute_step("Get Baseline Performance", get_baseline)
        print(f"📊 Baseline: avg={baseline.data['avg_response_time']:.3f}s")

        # Step 2: Generate sustained load
        def generate_sustained_load():
            duration_seconds = 10  # Shorter for testing
            requests_per_second = 5

            def make_request():
                try:
                    start = time.time()
                    response = requests.get("http://localhost:8080/metrics", timeout=5)
                    return {
                        "success": response.status_code == 200,
                        "duration": time.time() - start,
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}

            results = []
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                while time.time() - start_time < duration_seconds:
                    batch_start = time.time()
                    futures = [
                        executor.submit(make_request)
                        for _ in range(requests_per_second)
                    ]
                    batch_results = [f.result() for f in futures]
                    results.extend(batch_results)

                    elapsed = time.time() - batch_start
                    if elapsed < 1.0:
                        time.sleep(1.0 - elapsed)

            successful = [r for r in results if r.get("success")]
            response_times = [r["duration"] for r in successful]

            return {
                "total_requests": len(results),
                "successful": len(successful),
                "success_rate": len(successful) / len(results) * 100 if results else 0,
                "avg_response_time": sum(response_times) / len(response_times)
                if response_times
                else 0,
                "max_response_time": max(response_times) if response_times else 0,
            }

        load_result = self.execute_step(
            "Generate Sustained Load", generate_sustained_load
        )

        print("\nLoad Test Results:")
        print(f"  Total Requests: {load_result.data['total_requests']}")
        print(f"  Success Rate: {load_result.data['success_rate']:.2f}%")
        print(f"  Avg Response: {load_result.data['avg_response_time']:.3f}s")
        print(f"  Max Response: {load_result.data['max_response_time']:.3f}s")

        # Step 3: Verify targets
        assert load_result.data["success_rate"] > 95, "Success rate below 95%"
        assert load_result.data["avg_response_time"] < 2.0, "Average response > 2s"

        # Step 4: Check system metrics
        def check_system_metrics():
            time.sleep(2)
            metrics = {}

            response = prometheus_client.query("mcp_system_cpu_usage_percent")
            if response["status"] == "success" and response["data"]["result"]:
                metrics["cpu"] = float(response["data"]["result"][0]["value"][1])

            response = prometheus_client.query("mcp_system_memory_usage_bytes")
            if response["status"] == "success" and response["data"]["result"]:
                metrics["memory_mb"] = float(
                    response["data"]["result"][0]["value"][1]
                ) / (1024 * 1024)

            return metrics

        try:
            metrics_result = self.execute_step(
                "Check System Metrics", check_system_metrics
            )
            if "cpu" in metrics_result.data:
                print("\nSystem Metrics:")
                print(f"  CPU: {metrics_result.data['cpu']:.1f}%")
            if "memory_mb" in metrics_result.data:
                print(f"  Memory: {metrics_result.data['memory_mb']:.1f} MB")
        except Exception:
            print(
                "\n⚠️ Could not collect system metrics (Prometheus may not be available)"
            )

        self.print_results()
        print("\n✅ Sustained Load E2E Test PASSED!")
