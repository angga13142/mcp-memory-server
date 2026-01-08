"""Simple in-memory rate limiter for monitoring endpoints."""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    """Sliding-window rate limiter keyed by client identifier."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: defaultdict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> tuple[bool, int]:
        """Check if a request is allowed and return remaining quota."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[client_id] = [t for t in self._requests[client_id] if t > cutoff]
        request_count = len(self._requests[client_id])
        if request_count >= self.max_requests:
            return False, 0
        self._requests[client_id].append(now)
        remaining = self.max_requests - request_count - 1
        return True, remaining

    def get_retry_after(self, client_id: str) -> int:
        """Return seconds until the rate limit resets for a client."""
        if client_id not in self._requests or not self._requests[client_id]:
            return 0
        oldest = min(self._requests[client_id])
        reset_time = oldest + self.window_seconds
        return max(0, int(reset_time - time.time()))


__all__ = ["RateLimiter"]
