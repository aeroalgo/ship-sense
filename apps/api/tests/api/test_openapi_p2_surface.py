"""s20 OpenAPI contract is additive and exposes the stream surface."""

from app.main import app


def test_openapi_documents_p2_routes() -> None:
    paths = app.openapi()["paths"]

    assert "/api/reports/watch" in paths
    assert "/api/warnings" in paths
    assert "/api/warnings/history" in paths


def test_openapi_has_no_breaking_v2_namespace() -> None:
    assert all(not path.startswith("/api/v2") for path in app.openapi()["paths"])
