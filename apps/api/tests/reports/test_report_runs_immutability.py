from pathlib import Path


def test_report_runs_migration_contains_database_immutability_trigger() -> None:
    migration = Path("migrations/versions/007_report_runs.py").read_text()

    assert "BEFORE UPDATE OR DELETE ON report_runs" in migration
    assert "report_runs table is append-only" in migration
