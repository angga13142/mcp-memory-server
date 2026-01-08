"""Configuration for load tests."""

import asyncio

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "load: mark test as a load test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_load_test_environment():
    """Setup environment for load tests."""
    print("\n🔧 Setting up load test environment...")

    # Ensure services are running
    import time

    import requests

    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8080/health", timeout=2)
            if response.status_code == 200:
                print("✅ Application is ready")
                break
        except Exception:
            if i < max_retries - 1:
                print(f"⏳ Waiting for application...  ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                pytest.exit("❌ Application not available for load testing")

    yield

    print("\n🔧 Cleaning up load test environment...")
