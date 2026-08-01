"""Small cross-cutting middleware for API responses."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from time import monotonic, perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.settings import settings


def _parse_limit(value: str) -> tuple[int, float]:
    count, _, period = value.partition("/")
    seconds = {"s": 1.0, "sec": 1.0, "min": 60.0, "h": 3600.0}.get(period, 60.0)
    return max(1, int(count)), seconds


class RateLimitMiddleware:
    """Apply per-IP sliding-window limits to public REST scopes."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def _scope_limit(self, path: str) -> tuple[str, int, float] | None:
        if path == "/api/series" or path.startswith("/api/series/"):
            raw = settings.API_RATE_LIMIT_SERIES
            scope = "series"
        elif path == "/api/events" or path.startswith("/api/events/"):
            raw = settings.API_RATE_LIMIT_EVENTS
            scope = "events"
        elif path == "/api/session" or path.startswith("/api/session/"):
            raw = settings.API_RATE_LIMIT_SESSION
            scope = "session"
        else:
            raw = settings.API_RATE_LIMIT_GLOBAL
            scope = "global"
        limit, period = _parse_limit(raw)
        return scope, limit, period

    def _check(self, scope: Scope) -> tuple[bool, int, int, float]:
        configured = self._scope_limit(scope.get("path", ""))
        if configured is None:
            return True, 0, 0, 0.0
        bucket, limit, period = configured
        client = scope.get("client") or ("unknown", 0)
        key = (bucket, str(client[0]))
        now = monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] >= period:
            hits.popleft()
        remaining = max(0, limit - len(hits) - 1)
        if len(hits) >= limit:
            retry_after = max(1.0, period - (now - hits[0]))
            return False, limit, 0, retry_after
        hits.append(now)
        return True, limit, remaining, 0.0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        allowed, limit, remaining, retry_after = self._check(scope)
        if not allowed:
            body = json.dumps(
                {"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "details": None}}
            ).encode("utf-8")
            headers = [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"x-ratelimit-limit", str(limit).encode("ascii")),
                (b"x-ratelimit-remaining", b"0"),
                (b"retry-after", str(int(retry_after)).encode("ascii")),
            ]
            await send({"type": "http.response.start", "status": 429, "headers": headers})
            await send({"type": "http.response.body", "body": body})
            return

        async def send_with_rate_limit(message: Message) -> None:
            if message["type"] == "http.response.start" and limit:
                headers = list(message.get("headers", []))
                headers.extend(
                    (
                        (b"x-ratelimit-limit", str(limit).encode("ascii")),
                        (b"x-ratelimit-remaining", str(remaining).encode("ascii")),
                    )
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_rate_limit)


class RequestContextMiddleware:
    """Attach a request id and elapsed processing time to every response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        started = perf_counter()

        async def send_with_context(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    (
                        (b"x-request-id", request_id.encode("ascii")),
                        (
                            b"x-process-time",
                            f"{perf_counter() - started:.6f}".encode("ascii"),
                        ),
                    )
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_context)
