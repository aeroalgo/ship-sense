import pytest

from app.core.middleware import RateLimitMiddleware
from app.main import create_app


@pytest.mark.asyncio
async def test_series_burst_is_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr("app.core.middleware.settings.API_RATE_LIMIT_SERIES", "2/min")
    app = create_app()
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get("/api/series")
        second = await client.get("/api/series")
        third = await client.get("/api/series")

    assert first.headers["x-ratelimit-limit"] == "2"
    assert second.headers["x-ratelimit-remaining"] == "0"
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "RATE_LIMITED"
    assert third.headers["retry-after"]
