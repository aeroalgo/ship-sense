"""Create the samples TimescaleDB hypertable."""

from alembic import op


revision = "002_samples_hypertable"
down_revision = "001_extensions_timescale"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE samples (
            ts              TIMESTAMPTZ NOT NULL,
            tag_id          TEXT        NOT NULL,
            value           DOUBLE PRECISION,
            quality         SMALLINT    NOT NULL DEFAULT 0,
            source_ts       TIMESTAMPTZ NOT NULL,
            edge_ts         TIMESTAMPTZ NOT NULL,
            official_ts     TIMESTAMPTZ NOT NULL,
            CONSTRAINT samples_quality_chk CHECK (quality BETWEEN 0 AND 5),
            CONSTRAINT samples_pk PRIMARY KEY (tag_id, ts)
        )
        """
    )
    # Chunk interval is one day per CR-STO-01; benchmark validation is deferred.
    op.execute(
        """
        SELECT create_hypertable(
            'samples',
            'ts',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        )
        """
    )
    op.execute("CREATE INDEX idx_samples_tag_ts_desc ON samples (tag_id, ts DESC)")
    op.execute("CREATE INDEX idx_samples_official_ts ON samples (official_ts DESC)")
    op.execute("CREATE INDEX idx_samples_edge_ts ON samples (edge_ts DESC)")


def downgrade() -> None:
    op.execute("SELECT drop_chunks('samples', now())")
    op.execute("DROP TABLE IF EXISTS samples")
