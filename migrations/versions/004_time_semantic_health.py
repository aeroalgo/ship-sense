"""Create clock, semantic metadata, quarantine, and health tables."""

from alembic import op


revision = "004_time_semantic_health"
down_revision = "003_events_append_only"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE clock_shift_log (
            id              BIGSERIAL PRIMARY KEY,
            detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            detected_on     TEXT NOT NULL CHECK (detected_on IN ('edge', 'source')),
            delta           INTERVAL NOT NULL,
            prev_ts         TIMESTAMPTZ NOT NULL,
            new_ts          TIMESTAMPTZ NOT NULL,
            linked_event_id UUID REFERENCES events(event_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_clock_shift_detected ON clock_shift_log (detected_at DESC)"
    )
    op.execute(
        """
        CREATE TABLE semantic_meta (
            id           SERIAL PRIMARY KEY,
            pack_name    TEXT NOT NULL,
            version      TEXT NOT NULL,
            approved_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            checksum     TEXT NOT NULL,
            manifest     JSONB NOT NULL,
            UNIQUE (pack_name, version)
        )
        """
    )
    # CR-STO-03: quarantine acknowledgement is persisted for later quality UX.
    op.execute(
        """
        CREATE TABLE tag_quarantine (
            tag_id          TEXT PRIMARY KEY,
            reason          TEXT NOT NULL,
            since           TIMESTAMPTZ NOT NULL DEFAULT now(),
            native_id_hint  TEXT,
            acknowledged    BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_tag_quarantine_since ON tag_quarantine (since DESC)"
    )
    op.execute(
        """
        CREATE TABLE health_snapshots (
            id              BIGSERIAL PRIMARY KEY,
            captured_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            disk_total_gb   DOUBLE PRECISION,
            disk_used_gb    DOUBLE PRECISION,
            disk_pct        DOUBLE PRECISION,
            ram_pct         DOUBLE PRECISION,
            cpu_pct         DOUBLE PRECISION,
            samples_bytes   BIGINT,
            events_bytes    BIGINT,
            extra           JSONB DEFAULT '{}'
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_health_snapshots_at ON health_snapshots (captured_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS health_snapshots")
    op.execute("DROP TABLE IF EXISTS tag_quarantine")
    op.execute("DROP TABLE IF EXISTS semantic_meta")
    op.execute("DROP TABLE IF EXISTS clock_shift_log")
