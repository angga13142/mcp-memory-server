"""Base classes for E2E tests."""

import time
from dataclasses import dataclass
from typing import Any

import pytest
import requests


@dataclass
class E2ETestResult:
    """Result of an E2E test step."""

    step_name: str
    success: bool
    duration: float
    error: str | None = None
    data: dict[str, Any] | None = None


class E2ETestBase:
    """Base class for E2E tests."""

    results: list[E2ETestResult] = []
    test_data: dict[str, Any] = {}

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.results = []
        self.test_data = {}
        yield
        # Cleanup after test
        self._cleanup()

    def _cleanup(self):
        """Cleanup test data."""
        pass

    def execute_step(self, step_name: str, func, *args, **kwargs) -> E2ETestResult:
        """Execute a test step and record results."""
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            test_result = E2ETestResult(
                step_name=step_name,
                success=True,
                duration=duration,
                data=result if isinstance(result, dict) else None,
            )
        except Exception as e:
            duration = time.time() - start_time
            test_result = E2ETestResult(
                step_name=step_name, success=False, duration=duration, error=str(e)
            )

        self.results.append(test_result)

        if not test_result.success:
            pytest.fail(f"Step '{step_name}' failed: {test_result.error}")

        return test_result

    def print_results(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("E2E TEST RESULTS")
        print("=" * 60)

        total_duration = sum(r.duration for r in self.results)
        successful = sum(1 for r in self.results if r.success)

        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.step_name}: {result.duration:.2f}s")

        print("=" * 60)
        print(f"Total Steps: {len(self.results)}")
        print(f"Successful: {successful}/{len(self.results)}")
        print(f"Total Duration: {total_duration:.2f}s")
        print("=" * 60)


class APIClient:
    """Helper class for API interactions."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def get(self, path: str, **kwargs) -> requests.Response:
        """GET request."""
        url = f"{self.base_url}{path}"
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def post(self, path: str, **kwargs) -> requests.Response:
        """POST request."""
        url = f"{self.base_url}{path}"
        response = self.session.post(url, **kwargs)
        response.raise_for_status()
        return response

    def put(self, path: str, **kwargs) -> requests.Response:
        """PUT request."""
        url = f"{self.base_url}{path}"
        response = self.session.put(url, **kwargs)
        response.raise_for_status()
        return response

    def delete(self, path: str, **kwargs) -> requests.Response:
        """DELETE request."""
        url = f"{self.base_url}{path}"
        response = self.session.delete(url, **kwargs)
        response.raise_for_status()
        return response


class PrometheusClient:
    """Helper class for Prometheus interactions."""

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url

    def query(self, query: str) -> dict[str, Any]:
        """Execute Prometheus query."""
        response = requests.get(
            f"{self.base_url}/api/v1/query", params={"query": query}
        )
        response.raise_for_status()
        return response.json()

    def query_range(
        self, query: str, start: int, end: int, step: str = "15s"
    ) -> dict[str, Any]:
        """Execute Prometheus range query."""
        response = requests.get(
            f"{self.base_url}/api/v1/query_range",
            params={"query": query, "start": start, "end": end, "step": step},
        )
        response.raise_for_status()
        return response.json()

    def get_targets(self) -> dict[str, Any]:
        """Get Prometheus targets."""
        response = requests.get(f"{self.base_url}/api/v1/targets")
        response.raise_for_status()
        return response.json()

    def get_alerts(self) -> dict[str, Any]:
        """Get active alerts."""
        response = requests.get(f"{self.base_url}/api/v1/alerts")
        response.raise_for_status()
        return response.json()


class GrafanaClient:
    """Helper class for Grafana interactions."""

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        username: str = "admin",
        password: str = "admin",
    ):
        self.base_url = base_url
        self.auth = (username, password)

    def get_datasources(self) -> list[dict[str, Any]]:
        """Get all datasources."""
        response = requests.get(f"{self.base_url}/api/datasources", auth=self.auth)
        response.raise_for_status()
        return response.json()

    def get_dashboards(self) -> list[dict[str, Any]]:
        """Get all dashboards."""
        response = requests.get(
            f"{self.base_url}/api/search?type=dash-db", auth=self.auth
        )
        response.raise_for_status()
        return response.json()

    def get_dashboard(self, uid: str) -> dict[str, Any]:
        """Get specific dashboard."""
        response = requests.get(
            f"{self.base_url}/api/dashboards/uid/{uid}", auth=self.auth
        )
        response.raise_for_status()
        return response.json()

    def query_datasource(self, datasource_id: int, query: str) -> dict[str, Any]:
        """Query a datasource."""
        response = requests.get(
            f"{self.base_url}/api/datasources/proxy/{datasource_id}/api/v1/query",
            params={"query": query},
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()
