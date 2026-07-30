from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_health_stub_is_available_and_openapi_is_exposed() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health_response = await client.get("/api/health")
        openapi_response = await client.get("/openapi.json")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert openapi_response.status_code == 200
    assert "/api/health" in openapi_response.json()["paths"]
