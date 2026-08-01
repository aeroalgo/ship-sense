"""Create immutable report run history."""

from alembic import op


revision = "007_report_runs"
down_revision = "006_compression_retention"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE report_runs (
            report_id UUID NOT NULL,
            version INTEGER NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('watch', 'daily_noon', 'fuel', 'register')),
            period_from TIMESTAMPTZ NOT NULL,
            period_to TIMESTAMPTZ NOT NULL,
            boundary_rule TEXT NOT NULL,
            asset_scope TEXT,
            formulas_version TEXT NOT NULL,
            data_watermark TIMESTAMPTZ NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            initiated_by TEXT,
            body_json JSONB NOT NULL,
            body_html TEXT,
            provenance JSONB NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('final', 'preliminary')),
            PRIMARY KEY (report_id, version)
        )
        """
    )
    op.execute("CREATE INDEX report_runs_type_generated ON report_runs (type, generated_at DESC)")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION forbid_report_runs_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'report_runs table is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_report_runs_no_update
            BEFORE UPDATE OR DELETE ON report_runs
            FOR EACH ROW EXECUTE FUNCTION forbid_report_runs_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS report_runs")
    op.execute("DROP FUNCTION IF EXISTS forbid_report_runs_mutation()")
