"""Light in-memory fixed-window rate limiter (docs/03-lld.md §7).

MVP-scale only: state lives in-process, so it resets on restart and is per
instance, not shared across replicas. Enough to blunt casual spam on the
anonymous response endpoint. Swap for Redis if we ever scale out.
"""

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits = max_hits
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        bucket = [t for t in self._hits[key] if t > cutoff]
        bucket.append(now)
        self._hits[key] = bucket
        return len(bucket) <= self.max_hits


# Max 10 response submissions per IP+catchup per minute.
response_limiter = RateLimiter(max_hits=10, window_seconds=60.0)
