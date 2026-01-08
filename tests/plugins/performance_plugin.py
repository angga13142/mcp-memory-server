"""Pytest plugin for performance tracking."""

import pytest


class PerformanceTracker:
    """Track test performance."""

    def __init__(self):
        self.test_times: dict[str, float] = {}
        self.slow_tests: list[tuple] = []
        self.threshold: float = 1.0

    def record_test(self, test_name: str, duration: float):
        """Record test duration."""
        self.test_times[test_name] = duration

        if duration > self.threshold:
            self.slow_tests.append((test_name, duration))

    def get_report(self) -> str:
        """Generate performance report."""
        if not self.test_times:
            return "No tests recorded"

        total_time = sum(self.test_times.values())
        avg_time = total_time / len(self.test_times)

        report = [
            "\n" + "=" * 60,
            "TEST PERFORMANCE REPORT",
            "=" * 60,
            f"Total Tests: {len(self.test_times)}",
            f"Total Time: {total_time:.2f}s",
            f"Average Time: {avg_time:.2f}s",
            "",
        ]

        if self.slow_tests:
            report.append(f"Slow Tests (>{self.threshold}s):")
            for test_name, duration in sorted(
                self.slow_tests, key=lambda x: x[1], reverse=True
            ):
                report.append(f"  {duration:.2f}s - {test_name}")

        report.append("=" * 60)

        return "\n".join(report)


@pytest.fixture(scope="session")
def performance_tracker():
    """Performance tracker fixture."""
    return PerformanceTracker()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to track test performance."""
    outcome = yield

    if call.when == "call":
        outcome.get_result()

        if hasattr(item, "performance_tracker"):
            test_name = item.nodeid
            duration = call.duration
            item.performance_tracker.record_test(test_name, duration)


def pytest_sessionfinish(session, exitstatus):
    """Hook to print performance report."""
    if hasattr(session.config, "_performance_tracker"):
        tracker = session.config._performance_tracker
        print(tracker.get_report())
