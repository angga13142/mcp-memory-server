"""Custom assertions for tests."""

import time
from typing import Any


def assert_response_time(func, max_seconds: float = 1.0, *args, **kwargs):
    """Assert function completes within time limit."""
    start = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start

    assert (
        duration < max_seconds
    ), f"Function took {duration:.2f}s, expected < {max_seconds}s"
    return result


def assert_metric_value(
    metrics_text: str,
    metric_name: str,
    expected_min: float | None = None,
    expected_max: float | None = None,
):
    """Assert metric value is in expected range."""
    for line in metrics_text.split("\n"):
        if line.startswith(metric_name):
            try:
                value = float(line.split()[-1])

                if expected_min is not None:
                    assert (
                        value >= expected_min
                    ), f"{metric_name} = {value}, expected >= {expected_min}"

                if expected_max is not None:
                    assert (
                        value <= expected_max
                    ), f"{metric_name} = {value}, expected <= {expected_max}"

                return value
            except (ValueError, IndexError):
                pass

    raise AssertionError(f"Metric {metric_name} not found in metrics output")


def assert_prometheus_has_data(prometheus_client, metric_name: str):
    """Assert Prometheus has data for metric."""
    response = prometheus_client.query(metric_name)

    assert response["status"] == "success", f"Query failed for {metric_name}"
    assert len(response["data"]["result"]) > 0, f"No data for metric {metric_name}"

    return response


def assert_database_row_count(connection, table_name: str, expected_count: int):
    """Assert database table has expected row count."""
    cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
    actual_count = cursor.fetchone()[0]

    assert (
        actual_count == expected_count
    ), f"Table {table_name} has {actual_count} rows, expected {expected_count}"


def assert_contains_all(container, items: list[Any], message: str | None = None):
    """Assert container contains all items."""
    missing = [item for item in items if item not in container]

    if missing:
        msg = message or f"Missing items: {missing}"
        raise AssertionError(msg)


def assert_json_structure(data: dict[str, Any], expected_keys: list[str]):
    """Assert JSON has expected structure."""
    missing_keys = [key for key in expected_keys if key not in data]

    if missing_keys:
        raise AssertionError(f"Missing keys in JSON: {missing_keys}")


def assert_metric_increasing(values: list[float], tolerance: float = 0.0):
    """Assert metric values are increasing."""
    for i in range(1, len(values)):
        assert (
            values[i] >= values[i - 1] - tolerance
        ), f"Value decreased at index {i}: {values[i]} < {values[i-1]}"
