from collections.abc import Iterator

import pytest

from app.main import app


EXPECTED_OPERATIONS = {
    ("get", "/api/admin/access/audit"): ("getAdminAccessAudit", "admin"),
    ("get", "/api/admin/ota/status"): ("getAdminOtaStatus", "admin"),
    ("post", "/api/admin/ota/approve"): ("approveAdminOta", "admin"),
    ("post", "/api/admin/ota/trigger"): ("triggerAdminOta", "admin"),
    ("get", "/api/admin/storage"): ("getAdminStorage", "admin"),
    ("get", "/api/health"): ("getHealth", "health"),
    ("get", "/api/sources/status"): ("getSourcesStatus", "health"),
    ("get", "/api/reports/catalog"): ("getReportsCatalog", "reports"),
    ("get", "/api/reports"): ("getReports", "reports"),
    ("post", "/api/reports/generate"): ("generateReport", "reports"),
    ("post", "/api/reports/watch/generate"): ("generateWatchReport", "reports"),
    ("get", "/api/reports/jobs/{job_id}"): ("getReportJob", "reports"),
    ("get", "/api/reports/watch"): ("getWatchReport", "reports"),
    ("get", "/api/reports/{report_id}"): ("getReport", "reports"),
    ("get", "/api/reports/{report_id}/versions/{version}"): ("getReportVersion", "reports"),
    ("get", "/api/reports/{report_id}/versions/{version}/html"): ("getReportVersionHtml", "reports"),
    ("get", "/api/assets/tree"): ("getAssetsTree", "assets"),
    ("get", "/api/series"): ("getSeries", "series"),
    ("get", "/api/series/aggregate"): ("getSeriesAggregate", "series"),
    ("get", "/api/events"): ("getEvents", "events"),
    ("get", "/api/setpoints"): ("getSetpoints", "setpoints"),
    ("get", "/api/setpoints/history"): ("getSetpointHistory", "setpoints"),
    ("get", "/api/setpoints/changelog"): ("getSetpointChangelog", "setpoints"),
    ("get", "/api/watch/roster"): ("getWatchRoster", "session"),
    ("get", "/api/watch/schedule"): ("getWatchSchedule", "reports"),
    ("post", "/api/session"): ("createSession", "session"),
    ("delete", "/api/session"): ("deleteSession", "session"),
    ("get", "/api/warnings"): ("getWarnings", "warnings"),
    ("get", "/api/warnings/history"): ("getWarningsHistory", "warnings"),
    ("get", "/api/mnemo/schemas"): ("getMnemoSchemas", "mnemo"),
    ("get", "/api/mnemo/schemas/{schema_id}"): ("getMnemoSchema", "mnemo"),
    ("get", "/api/mnemo/schemas/{schema_id}/values"): ("getMnemoValues", "mnemo"),
    ("get", "/api/vessel/state"): ("getVesselState", "vessel"),
    ("post", "/api/vessel/state/override"): ("overrideVesselState", "vessel"),
}


def _descriptions(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        description = value.get("description")
        if isinstance(description, str):
            yield description
        for child in value.values():
            yield from _descriptions(child)
    elif isinstance(value, list):
        for child in value:
            yield from _descriptions(child)


@pytest.fixture
def openapi_spec() -> dict:
    return app.openapi()


def test_openapi_documents_expected_p2_rest_surface(openapi_spec: dict) -> None:
    paths = openapi_spec["paths"]

    assert set(paths) == {path for _, path in EXPECTED_OPERATIONS}
    for (method, path), (operation_id, tag) in EXPECTED_OPERATIONS.items():
        operation = paths[path][method]
        assert operation["operationId"] == operation_id
        assert operation["tags"] == [tag]


def test_openapi_allows_only_declared_p2_mutations(openapi_spec: dict) -> None:
    mutations = {
        (method, path)
        for path, path_item in openapi_spec["paths"].items()
        for method in path_item
        if method in {"post", "put", "patch", "delete"}
    }

    assert mutations == {
        ("post", "/api/admin/ota/approve"),
        ("post", "/api/admin/ota/trigger"),
        ("post", "/api/reports/generate"),
        ("post", "/api/reports/watch/generate"),
        ("post", "/api/session"),
        ("delete", "/api/session"),
        ("post", "/api/vessel/state/override"),
    }


def test_openapi_exposes_quarantine_quality_example(openapi_spec: dict) -> None:
    quality = openapi_spec["components"]["schemas"]["Quality"]
    series_point = openapi_spec["components"]["schemas"]["SeriesPoint"]

    assert "quarantine" in quality["enum"]
    assert series_point["properties"]["quality"]["examples"] == ["quarantine"]


def test_openapi_descriptions_do_not_claim_ai(openapi_spec: dict) -> None:
    forbidden = ("sklearn", "tensorflow", "machine learning", "artificial intelligence", "ии")
    assert all(
        not any(term in description.lower() for term in forbidden)
        for description in _descriptions(openapi_spec)
    )
