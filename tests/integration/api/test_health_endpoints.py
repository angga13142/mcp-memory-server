"""Integration tests for health endpoints."""

import concurrent.futures
import time

import pytest
import requests


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL."""
        return "http://localhost:8080"

    @pytest.fixture(scope="class", autouse=True)
    def ensure_server_available(self, base_url):
        """Skip if server is not available."""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not healthy")
        except requests.exceptions.RequestException:
            pytest.skip("Server not running")

    def test_health_endpoint_exists(self, base_url):
        """Test /health endpoint exists."""
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200

    def test_health_endpoint_response_format(self, base_url):
        """Test /health response format."""
        response = requests.get(f"{base_url}/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "ok", "up"]

    def test_health_endpoint_details(self, base_url):
        """Test /health includes service details."""
        response = requests.get(f"{base_url}/health")
        data = response.json()

        # Should include component health if available
        if "components" in data:
            assert "database" in data["components"] or "db" in data["components"]

    def test_readiness_endpoint(self, base_url):
        """Test /ready or /readiness endpoint."""
        # Try common readiness endpoint paths
        for path in ["/ready", "/readiness", "/health/ready"]:
            try:
                response = requests.get(f"{base_url}{path}", timeout=2)
                if response.status_code == 200:
                    return  # Success
            except requests.exceptions.RequestException:
                continue

        # If no readiness endpoint, that's ok (optional)
        pytest.skip("No readiness endpoint found (optional)")

    def test_liveness_endpoint(self, base_url):
        """Test /live or /liveness endpoint."""
        for path in ["/live", "/liveness", "/health/live"]:
            try:
                response = requests.get(f"{base_url}{path}", timeout=2)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                continue

        pytest.skip("No liveness endpoint found (optional)")

    def test_health_endpoint_performance(self, base_url):
        """Test health endpoint responds quickly."""
        start = time.time()
        response = requests.get(f"{base_url}/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5  # Should respond in < 500ms

    def test_health_endpoint_concurrent_requests(self, base_url):
        """Test health endpoint handles concurrent requests."""

        def check_health():
            response = requests.get(f"{base_url}/health", timeout=5)
            return response.status_code == 200

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(20)]
            results = [f.result() for f in futures]

        assert all(results), "Some health checks failed"
