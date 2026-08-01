"""Create B13 active and warning history tables."""

from alembic import op


revision = "008_warnings"
down_revision = "007_report_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE warnings_active (
            tag_id TEXT PRIMARY KEY,
            asset_id TEXT,
            status TEXT NOT NULL CHECK (status IN ('active', 'cleared')),
            raw_value DOUBLE PRECISION NOT NULL,
            ewma_value DOUBLE PRECISION NOT NULL,
            setpoint DOUBLE PRECISION NOT NULL,
            setpoint_source TEXT NOT NULL,
            unit TEXT NOT NULL,
            threshold_pct DOUBLE PRECISION NOT NULL,
            comparison TEXT NOT NULL CHECK (comparison IN ('high', 'low')),
            slope_per_hour DOUBLE PRECISION,
            eta_to_setpoint_days DOUBLE PRECISION,
            quality SMALLINT NOT NULL DEFAULT 0,
            suppressed_reason TEXT,
            since TIMESTAMPTZ NOT NULL,
            config_version TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE warnings_history (
            id BIGSERIAL PRIMARY KEY,
            tag_id TEXT NOT NULL,
            from_status TEXT NOT NULL,
            to_status TEXT NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL,
            warning_json JSONB NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX warnings_history_tag_occurred ON warnings_history (tag_id, occurred_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS warnings_history")
    op.execute("DROP TABLE IF EXISTS warnings_active")
