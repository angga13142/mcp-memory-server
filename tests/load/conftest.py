"""Configuration for load tests."""

import asyncio

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "load: mark test as a load test")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
