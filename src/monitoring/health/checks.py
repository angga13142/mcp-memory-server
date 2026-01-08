"""
Module: checks.py

Description:
    Lightweight health check helpers for the monitoring package. These
    utilities can be used by HTTP or CLI health endpoints to aggregate
    readiness and liveness information.

Usage:
    async def database_check():
        ...
    results = await run_health_checks({"database": database_check})

Author: GitHub Copilot
Date: 2026-01-08
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable


async def run_health_checks(
    checks: dict[str, Callable[[], Awaitable[bool]]],
) -> dict[str, bool]:
    """Run each asynchronous health check and return boolean results."""
    results: dict[str, bool] = {}
    for name, check in checks.items():
        try:
            results[name] = await check()
        except Exception:
            results[name] = False
    return results


def summarize_health(results: dict[str, bool]) -> dict[str, object]:
    """Summarize health results with overall status."""
    overall = all(results.values()) if results else False
    return {"ok": overall, "checks": results}


__all__ = ["run_health_checks", "summarize_health"]
