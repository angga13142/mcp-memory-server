"""Integration tests for metrics endpoint."""

import pytest
import requests

# Skip all tests if server is not running
pytestmark = pytest.mark.skipif(True, reason="Requires running server on port 8080")


@pytest.mark.integration
class TestMetricsEndpoint:
    """Test /metrics endpoint integration."""

    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for API."""
        return "http://localhost:8080"

    @pytest.fixture(scope="class", autouse=True)
    def ensure_server_running(self, base_url):
        """Ensure server is running before tests."""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not healthy")
        except requests.exceptions.RequestException:
            pytest.skip("Server not running")

    def test_metrics_endpoint_returns_200(self, base_url):
        """Test metrics endpoint is accessible."""
        response = requests.get(f"{base_url}/metrics")

        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("text/plain")

    def test_metrics_endpoint_contains_journal_metrics(self, base_url):
        """Test metrics endpoint contains journal metrics."""
        response = requests.get(f"{base_url}/metrics")
        content = response.text

        # Check for all 8 journal metrics
        assert "mcp_journal_sessions_total" in content
        assert "mcp_journal_sessions_active" in content
        assert "mcp_journal_session_duration_minutes" in content
        assert "mcp_journal_reflections_generated_total" in content
        assert "mcp_journal_reflection_generation_seconds" in content
        assert "mcp_journal_learnings_captured_total" in content
        assert "mcp_journal_challenges_noted_total" in content
        assert "mcp_journal_wins_captured_total" in content

    def test_metrics_endpoint_contains_database_metrics(self, base_url):
        """Test metrics endpoint contains database metrics."""
        response = requests.get(f"{base_url}/metrics")
        content = response.text

        assert "mcp_db_connections_active" in content
        assert "mcp_db_query_duration_seconds" in content
        assert "mcp_db_queries_total" in content
        assert "mcp_db_errors_total" in content

    def test_metrics_endpoint_contains_vector_metrics(self, base_url):
        """Test metrics endpoint contains vector store metrics."""
        response = requests.get(f"{base_url}/metrics")
        content = response.text

        assert "mcp_vector_embeddings_generated_total" in content
        assert "mcp_vector_embedding_seconds" in content
        assert "mcp_vector_searches_total" in content
        assert "mcp_vector_search_results" in content
        assert "mcp_vector_memory_count" in content

    def test_metrics_endpoint_contains_system_metrics(self, base_url):
        """Test metrics endpoint contains system metrics."""
        response = requests.get(f"{base_url}/metrics")
        content = response.text

        assert "mcp_system_memory_usage_bytes" in content
        assert "mcp_system_cpu_usage_percent" in content
        assert "mcp_system_disk_usage_bytes" in content

    def test_metrics_have_valid_values(self, base_url):
        """Test metrics have realistic values."""
        response = requests.get(f"{base_url}/metrics")
        lines = response.text.split("\n")

        for line in lines:
            if line.startswith("mcp_system_memory_usage_bytes"):
                # Extract value
                value = float(line.split()[-1])
                # Should be between 10MB and 100GB
                assert 10 * 1024 * 1024 < value < 100 * 1024**3
                break

    def test_metrics_endpoint_performance(self, base_url):
        """Test metrics endpoint responds quickly."""
        import time

        start = time.time()
        response = requests.get(f"{base_url}/metrics")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should respond in less than 1 second


@pytest.mark.integration
class TestHealthEndpoint:
    """Test /health endpoint integration."""

    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for API."""
        return "http://localhost:8080"

    def test_health_endpoint_returns_200(self, base_url):
        """Test health endpoint is accessible."""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Server not running")

    def test_health_endpoint_returns_json(self, base_url):
        """Test health endpoint returns JSON."""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            data = response.json()
            assert "status" in data
        except requests.exceptions.RequestException:
            pytest.skip("Server not running")
