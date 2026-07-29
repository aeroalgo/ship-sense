"""Create storage quota and sample degradation audit tables."""

from alembic import op


revision = "005_quota_degrade"
down_revision = "004_time_semantic_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE storage_quota_config (
            id                SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            disk_total_bytes  BIGINT NOT NULL,
            alert_pct         DOUBLE PRECISION NOT NULL DEFAULT 80.0,
            samples_quota_pct DOUBLE PRECISION NOT NULL DEFAULT 85.0,
            events_quota_pct  DOUBLE PRECISION NOT NULL DEFAULT 10.0,
            headroom_pct      DOUBLE PRECISION NOT NULL DEFAULT 5.0,
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        INSERT INTO storage_quota_config (disk_total_bytes)
        VALUES (8589934592000)
        ON CONFLICT (id) DO NOTHING
        """
    )
    op.execute(
        """
        CREATE TABLE samples_degrade_log (
            id            BIGSERIAL PRIMARY KEY,
            degraded_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            chunk_start   TIMESTAMPTZ NOT NULL,
            chunk_end     TIMESTAMPTZ NOT NULL,
            reason        TEXT NOT NULL,
            rows_estimate BIGINT
        )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_samples_degrade_log_at
            ON samples_degrade_log (degraded_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE samples_degrade_watermark (
            id                SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            oldest_sample_ts  TIMESTAMPTZ,
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS samples_degrade_watermark")
    op.execute("DROP TABLE IF EXISTS samples_degrade_log")
    op.execute("DROP TABLE IF EXISTS storage_quota_config")
