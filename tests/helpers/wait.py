"""Wait helpers for tests."""

import time
from collections.abc import Callable
from typing import Any


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 0.5,
    error_message: str = "Condition not met within timeout",
) -> bool:
    """Wait for condition to become true."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)

    raise TimeoutError(error_message)


def wait_for_value(
    getter: Callable[[], Any],
    expected_value: Any,
    timeout: float = 30.0,
    interval: float = 0.5,
) -> Any:
    """Wait for getter to return expected value."""

    def condition():
        return getter() == expected_value

    wait_for_condition(
        condition,
        timeout,
        interval,
        f"Value did not become {expected_value} within {timeout}s",
    )

    return expected_value


def wait_for_service(
    health_check: Callable[[], bool],
    service_name: str = "service",
    timeout: float = 60.0,
) -> bool:
    """Wait for service to become healthy."""
    return wait_for_condition(
        health_check,
        timeout,
        interval=2.0,
        error_message=f"{service_name} did not become healthy within {timeout}s",
    )


def wait_for_metric_update(
    prometheus_client,
    metric_name: str,
    timeout: float = 30.0,
) -> bool:
    """Wait for Prometheus metric to update."""

    def condition():
        try:
            response = prometheus_client.query(metric_name)
            return (
                response["status"] == "success" and len(response["data"]["result"]) > 0
            )
        except Exception:
            return False

    return wait_for_condition(
        condition,
        timeout,
        interval=2.0,
        error_message=f"Metric {metric_name} not available within {timeout}s",
    )
