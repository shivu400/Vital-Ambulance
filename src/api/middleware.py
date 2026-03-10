"""Middleware for logging and basic rate limiting."""

from __future__ import annotations

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SimpleRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.calls = calls
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        now = time.time()
        timestamps = self._store.get(client, [])
        # keep only recent timestamps
        timestamps = [t for t in timestamps if now - t < self.window_seconds]
        if len(timestamps) >= self.calls:
            return Response(status_code=429, content="Rate limit exceeded")
        timestamps.append(now)
        self._store[client] = timestamps
        response = await call_next(request)
        return response
