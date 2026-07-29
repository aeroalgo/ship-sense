"""Create the append-only events store."""

from alembic import op


revision = "003_events_append_only"
down_revision = "002_samples_hypertable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE events (
            event_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            idempotency_key  TEXT NOT NULL UNIQUE,
            event_name       TEXT NOT NULL,
            source           TEXT NOT NULL,
            source_ts        TIMESTAMPTZ NOT NULL,
            edge_ts          TIMESTAMPTZ NOT NULL,
            official_ts      TIMESTAMPTZ NOT NULL,
            params           JSONB NOT NULL DEFAULT '{}',
            severity         SMALLINT,
            reconstructed    BOOLEAN NOT NULL DEFAULT FALSE,
            ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT events_severity_chk
                CHECK (severity IS NULL OR severity BETWEEN 0 AND 4)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_events_official_ts
            ON events (official_ts DESC, event_id)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_events_name_ts
            ON events (event_name, official_ts DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_events_source_ts
            ON events (source, official_ts DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_events_params_tag
            ON events ((params->>'tag_id'), official_ts DESC)
            WHERE params ? 'tag_id'
        """
    )
    op.execute(
        """
        CREATE INDEX idx_events_lifecycle_active
            ON events (official_ts DESC)
            WHERE event_name = 'alarm'
              AND (params->>'lifecycle') IN ('active', 'cleared', 'acked')
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION forbid_events_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'events table is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_events_no_update
            BEFORE UPDATE OR DELETE ON events
            FOR EACH ROW EXECUTE FUNCTION forbid_events_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS events")
    op.execute("DROP FUNCTION IF EXISTS forbid_events_mutation()")
