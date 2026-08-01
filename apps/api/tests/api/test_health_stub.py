from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_health_stub_is_available_and_openapi_is_exposed() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health_response = await client.get("/api/health")
        docs_response = await client.get("/api/docs")
        openapi_response = await client.get("/api/openapi.json")
        missing_response = await client.get("/api/missing")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert "/api/health" in openapi_response.json()["paths"]
    assert missing_response.status_code == 404
    assert missing_response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Not Found",
            "details": None,
        }
    }
    assert missing_response.headers["x-request-id"]
    assert "x-process-time" in missing_response.headers
