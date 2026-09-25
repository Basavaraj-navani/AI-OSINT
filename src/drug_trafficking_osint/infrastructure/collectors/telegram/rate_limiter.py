"""Rate limiting for Telegram API requests."""

from __future__ import annotations

import asyncio
import time
from collections import deque

from drug_trafficking_osint.infrastructure.collectors.telegram._types import (
    TelethonFloodWaitError,
)


class RateLimiter:
    """Token bucket rate limiter with FloodWait handling."""

    def __init__(
        self,
        requests_per_second: float = 30,
        burst: int = 50,
    ):
        self._rate = requests_per_second
        self._burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
        self._request_times: deque[float] = deque()

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(
                self._burst,
                self._tokens + (now - self._last_update) * self._rate,
            )
            self._last_update = now

            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1

            self._request_times.append(now)
            self._clean_old_requests()

    def _clean_old_requests(self) -> None:
        """Remove request times older than 1 second."""
        cutoff = time.monotonic() - 1
        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()

    async def handle_flood_wait(self, error: TelethonFloodWaitError) -> None:
        """Handle FloodWaitError by sleeping for the required duration."""
        wait_time = error.seconds
        if wait_time > 0:
            await asyncio.sleep(wait_time + 1)

    @property
    def requests_last_second(self) -> int:
        """Get number of requests in the last second."""
        return len(self._request_times)
