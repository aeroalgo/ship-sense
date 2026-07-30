from pathlib import Path

import yaml


def test_compose_uses_real_storage_writer_and_database_health_dependency():
    compose = yaml.safe_load(Path("docker-compose.yml").read_text())
    services = compose["services"]

    assert services["writer"]["build"]["context"] == "."
    assert services["writer"]["build"]["dockerfile"] == "apps/edge/storage/Dockerfile"
    assert services["writer"]["entrypoint"] == ["python", "-m", "apps.edge.storage"]
    assert services["writer"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["collector"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["collector"]["environment"]["SHIPSSENSE_WRITER_ENDPOINT"] == "writer:9009"
    assert services["db"]["healthcheck"]["test"][0] == "CMD-SHELL"


def test_storage_package_exports_writer_and_semantic_engine():
    from app.semantic.engine import SemanticEngine
    from apps.edge.storage import SamplesRepo, SemanticEngine as ExportedEngine, WriterService

    assert SamplesRepo is not None
    assert WriterService is not None
    assert ExportedEngine is SemanticEngine


def test_storage_image_exposes_collector_src_package_for_writer_imports():
    dockerfile = Path("apps/edge/storage/Dockerfile").read_text()

    assert "COPY apps/edge/collector/src/ ./collector/" in dockerfile
    assert "PYTHONPATH=/app:/app/collector" in dockerfile


def test_storage_migrations_use_installed_psycopg_driver():
    from apps.edge.storage.__main__ import migration_database_url

    assert migration_database_url(
        "postgresql+asyncpg://shipsense:shipsense@db:5432/shipsense"
    ) == "postgresql+psycopg://shipsense:shipsense@db:5432/shipsense"
