"""Enable TimescaleDB compression and retention policies on samples hypertable."""

from alembic import op

revision = "006_compression_retention"
down_revision = "005_quota_degrade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure search path is set
    op.execute("SET search_path TO shipsense, public")
    
    # Enable compression on samples hypertable
    op.execute(
        """
        ALTER TABLE samples SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'tag_id',
            timescaledb.compress_orderby = 'ts DESC'
        )
        """
    )
    
    op.execute(
        "SELECT add_compression_policy('samples', INTERVAL '7 days', if_not_exists => true)"
    )
    op.execute(
        "SELECT add_retention_policy('samples', INTERVAL '1095 days', if_not_exists => true)"
    )


def downgrade() -> None:
    # Ensure search path is set
    op.execute("SET search_path TO shipsense, public")
    
    # Remove policies before disabling compression
    op.execute("SELECT remove_retention_policy('samples', if_exists => true)")
    op.execute("SELECT remove_compression_policy('samples', if_exists => true)")
    
    # Disable compression on samples hypertable
    op.execute("ALTER TABLE samples SET (timescaledb.compress = false)")
