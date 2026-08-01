# ShipSense API

Scaffolded according to the `fastapi-templates` layout. Domain ownership moves into this package in later refactor steps; this scaffold intentionally exposes only the health stub.

I1 minimal: the read-only API exposes `/api/health`, `/api/docs`, `/api/openapi.json`, and `/api/redoc`; error responses use the shared `{"error": {"code", "message", "details"}}` envelope. This does not replace the full I1 protocol barrier.

The OpenAPI document is the REST contract for the phase-1 UI. Only session lifecycle mutates state; telemetry, events, setpoints, and reports remain read-only.

Run the API from the repository root with `PYTHONPATH=apps/api` and an ASGI server such as Uvicorn.

## ORM and migrations policy — phase 1

- SQLAlchemy tables and `Base.metadata` remain owned by `apps/edge/storage/schemas.py`.
- The active Alembic chain remains the repository-level `migrations/` configured by `alembic.ini`.
- `apps/api/migrations/` is only a reserved scaffold; it is not an active Alembic path and does not own DDL.
- The API may read the storage ORM through repositories and may import the storage schema during this transition.
- Moving the storage Alembic chain or introducing a second `DeclarativeBase` is out of scope for this phase.
