"""Simple in-memory rate limiter for login endpoint."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Hashable

from api.config import settings


class SlidingWindowRateLimiter:
    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._events: defaultdict[Hashable, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: Hashable) -> tuple[bool, int]:
        now = time.time()
        async with self._lock:
            queue = self._events[key]
            while queue and now - queue[0] > self.window_seconds:
                queue.popleft()

            if len(queue) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - queue[0])))
                return False, retry_after

            queue.append(now)
            return True, 0

    async def reset(self, key: Hashable) -> None:
        async with self._lock:
            self._events.pop(key, None)


login_rate_limiter = SlidingWindowRateLimiter(
    limit=settings.login_rate_limit,
    window_seconds=settings.login_rate_window_seconds,
)

