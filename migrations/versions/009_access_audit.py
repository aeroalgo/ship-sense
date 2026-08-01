"""Create append-only access audit history."""

from alembic import op


revision = "009_access_audit"
down_revision = "008_warnings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE access_audit (
            id BIGSERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            person_id TEXT,
            session_id UUID,
            action TEXT NOT NULL,
            source_ip INET,
            details JSONB NOT NULL DEFAULT '{}'
        )
        """
    )
    op.execute("CREATE INDEX access_audit_ts_id ON access_audit (ts DESC, id DESC)")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION forbid_access_audit_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'access_audit table is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_access_audit_no_update
            BEFORE UPDATE OR DELETE ON access_audit
            FOR EACH ROW EXECUTE FUNCTION forbid_access_audit_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS access_audit")
    op.execute("DROP FUNCTION IF EXISTS forbid_access_audit_mutation()")
